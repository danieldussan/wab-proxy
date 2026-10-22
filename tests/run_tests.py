#!/usr/bin/env python3
"""Pruebas de wa-proxy (solo librería estándar; funcionan igual en Linux/macOS/Windows).

Uso:  python tests/run_tests.py
Trabajan en una carpeta temporal (WA_ROOT): nunca tocan tu .env ni tu hosts.conf.
"""
import json, os, re, socket, stat, subprocess, sys, tempfile, threading, time, unittest, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix="wa-test-")
os.environ["WA_ROOT"] = TMP
os.environ["WA_SSH_KEY"] = os.path.join(TMP, "nokey")
sys.path.insert(0, REPO)

from wa_proxy import agent, core, dashboard   # noqa: E402

SOCKS = [(19101, "usr", "p@ss:w/rd#1"), (19102, "usr2", "x")]
procs = []
SERVER = None


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def internet():
    try:
        socket.create_connection(("api.ipify.org", 443), timeout=5).close()
        return True
    except OSError:
        return False


def reset_files():
    for f in (core.ENV_FILE, core.HOSTS_FILE):
        if os.path.exists(f):
            os.remove(f)


def setUpModule():
    global SERVER
    for port, u, p in SOCKS:
        procs.append(subprocess.Popen([sys.executable, os.path.join(HERE, "fake_socks5.py"), str(port), u, p]))
    SERVER = dashboard.Server(free_port(), "ui-token-test", "agent-token-test")
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()
    dashboard.write_session(SERVER.port, SERVER.agent_token)
    time.sleep(0.8)


def tearDownModule():
    SERVER.shutdown()
    for p in procs:
        p.terminate()


def http(path, body=None, ui=True, token=None, headers=None):
    hdr = {"Content-Type": "application/json", "Host": f"127.0.0.1:{SERVER.port}", **(headers or {})}
    hdr["X-Token" if ui else "X-Agent-Token"] = token if token is not None else (SERVER.ui_token if ui else SERVER.agent_token)
    req = urllib.request.Request(f"http://127.0.0.1:{SERVER.port}{path}", headers=hdr,
                                 data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def wa_agent(*args, timeout=60):
    """Ejecuta `wa agent ...` como lo haría un agente. -> Popen"""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.Popen([sys.executable, os.path.join(REPO, "wa.py"), "agent", *args], env=env, cwd=TMP,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def wait_pending(kind=None, n=40):
    for _ in range(n):
        for r in dashboard.HUB.pending_requests():
            if kind is None or r["kind"] == kind:
                return r
        time.sleep(0.25)
    raise AssertionError("no apareció la solicitud pendiente")


class Core(unittest.TestCase):
    def setUp(self):
        reset_files()

    def test_accounts_env_and_secrets(self):
        accs = [{"n": None, "label": 'Ventas "x" $(rm)', "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1"},
                {"n": None, "label": "", "host": "127.0.0.1", "port": "19102", "user": "usr2", "password": "x"}]
        core.save_accounts(accs)
        txt = open(core.ENV_FILE, encoding="utf-8").read()
        self.assertIn('PROXY_1="socks5://usr:p%40ss%3Aw%2Frd%231@127.0.0.1:19101"', txt)
        self.assertNotIn("$(", txt)
        if not core.IS_WIN:
            self.assertEqual(stat.S_IMODE(os.stat(core.ENV_FILE).st_mode), 0o600)
        self.assertNotIn("p@ss", json.dumps(core.public_accounts()))
        cur = [dict(a, password="") for a in core.public_accounts()]
        core.save_accounts(cur)                                      # contraseña vacía = conservar
        self.assertIn("p%40ss%3Aw%2Frd%231", open(core.ENV_FILE, encoding="utf-8").read())
        with self.assertRaises(core.ApiError):
            core.save_accounts([{"n": 1, "host": "a b;rm", "port": 1, "user": "u", "password": "p"}])
        with self.assertRaises(core.ApiError):
            core.save_accounts([{"n": None, "host": "h.com", "port": 1, "user": "u"}])
        s = core.scrubber()("error con p@ss:w/rd#1 y p%40ss%3Aw%2Frd%231 en socks5://usr:abc@h:1")
        self.assertNotIn("rd#1", s)
        self.assertNotIn("%2Frd", s)
        self.assertNotIn("abc", s)

    def test_upsert_keeps_numbers(self):
        n1, _ = core.upsert_account({"label": "A", "host": "h.com", "port": 1, "user": "u", "password": "pppp"})
        n2, _ = core.upsert_account({"label": "B", "host": "h.com", "port": 2, "user": "u", "password": "pppp"})
        self.assertEqual((n1, n2), (1, 2))
        n, accs = core.upsert_account({"n": 1, "label": "A2", "host": "h.com", "port": 1, "user": "u", "password": ""})
        self.assertEqual(n, 1)
        self.assertEqual([a["label"] for a in accs], ["A2", "B"])

    def test_compose_gaps_and_ports(self):
        core.save_accounts([{"n": 1, "host": "h.com", "port": 1, "user": "u", "password": "pppp"},
                            {"n": 3, "host": "h.com", "port": 3, "user": "u", "password": "pppp"}])
        c = core.generate_compose()
        self.assertIn("gw-1:", c)
        self.assertIn("gw-3:", c)
        self.assertNotIn("gw-2:", c)
        self.assertIn("5103:5222", c)
        self.assertIn("ginuerzh/gost:2.12.0", c)
        self.assertNotIn("pppp", c)                                  # el compose no lleva secretos
        with self.assertRaises(core.ApiError):
            reset_files()
            core.generate_compose()

    def test_vps_validation(self):
        core.add_vps({"ip": "203.0.113.9"})
        with self.assertRaises(core.ApiError):
            core.add_vps({"ip": "1.2.3.4; rm -rf /"})
        with self.assertRaises(core.ApiError):
            core.add_vps({"ip": "203.0.113.9"})
        self.assertIn("vps1=wa@203.0.113.9", open(core.HOSTS_FILE, encoding="utf-8").read())
        with self.assertRaises(core.ApiError):
            core.power(core.find_host("vps1"), 1, "rm -rf")
        with self.assertRaises(core.ApiError):
            core.power(core.find_host("vps1"), "1;ls", "stop")

    @unittest.skipUnless(internet(), "sin internet")
    def test_verify_and_partial_gateway(self):
        core.save_accounts([{"n": None, "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1"},
                            {"n": None, "host": "127.0.0.1", "port": 19102, "user": "usr2", "password": "x"}])
        ok, res = core.verify_accounts(lambda s: None)
        self.assertEqual(len(res["accounts"]), 2)
        for a in res["accounts"]:
            self.assertTrue(core.account_ok(a), a)
        self.assertTrue(res["duplicate_ips"])                        # ambos SOCKS de prueba salen por la misma IP
        self.assertFalse(ok)
        acc = {"n": 1, "label": "", "host": "127.0.0.1", "port": 19101, "enc_user": "usr", "enc_pass": "p%40ss%3Aw%2Frd%231"}
        orig = core.resolve_gateways
        try:
            core.resolve_gateways = lambda h: ["127.0.0.1", "127.0.0.2"]   # en 127.0.0.2 no escucha nadie
            r = core.check_account(acc, "api.ipify.org")
            self.assertTrue(r["partial"], r)
            self.assertEqual([g["ok"] for g in r["gateways"]], [True, False])
            self.assertFalse(core.account_ok(r))
            core.resolve_gateways = lambda h: ["127.0.0.1"]
            r = core.check_account(acc, "api.ipify.org")
            self.assertFalse(r["partial"])
            self.assertTrue(core.account_ok(r))
        finally:
            core.resolve_gateways = orig

    def test_wrong_password_is_reported(self):
        core.save_accounts([{"n": None, "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "mala-clave"}])
        accounts, _, _ = core.read_env()
        r = core.check_gateway(accounts[1], "api.ipify.org", "127.0.0.1")
        self.assertFalse(r["ok"])
        self.assertIn("rechazados", r["error"])


@unittest.skipIf(core.IS_WIN, "usa un ssh falso de shell")
class FakeSsh(unittest.TestCase):
    """Sustituye `ssh` por un script que registra lo que recibe: comprueba qué se sube a la VPS."""

    def setUp(self):
        reset_files()
        self.bin = os.path.join(TMP, "bin")
        self.log = os.path.join(TMP, "ssh.log")
        os.makedirs(self.bin, exist_ok=True)
        open(self.log, "w").close()
        with open(os.path.join(self.bin, "ssh"), "w") as f:
            f.write('#!/bin/sh\n'
                    'echo "ARGS: $*" >> "$WA_FAKE_LOG"\n'
                    'if [ -t 0 ]; then :; else cat | sed "s/^/IN: /" >> "$WA_FAKE_LOG"; fi\n'
                    'case "$*" in *"echo TSIP"*) ;; esac\nexit 0\n')
        os.chmod(os.path.join(self.bin, "ssh"), 0o755)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = self.bin + os.pathsep + self.old_path
        os.environ["WA_FAKE_LOG"] = self.log

    def tearDown(self):
        os.environ["PATH"] = self.old_path

    def test_deploy_uploads_files(self):
        core.save_accounts([{"n": 2, "host": "h.com", "port": 1, "user": "u", "password": "s3cr3t-pw"}])
        core.add_vps({"ip": "203.0.113.9"})
        lines = []
        self.assertTrue(core.deploy("vps1", log=lines.append))
        log = open(self.log, encoding="utf-8").read()
        self.assertIn("cat > wa-proxy/docker-compose.yml", log)
        self.assertIn("IN:   gw-2:", log)
        self.assertIn("umask 077; cat > wa-proxy/.env", log)
        self.assertIn('IN: PROXY_2="socks5://u:s3cr3t-pw@h.com:1"', log)
        self.assertIn("set -euo pipefail", log)                      # script de aplicar
        self.assertNotIn("s3cr3t-pw", "\n".join(lines))              # nunca en la salida visible

    def test_prepare_installs_key_and_bootstrap(self):
        lines = []
        self.assertTrue(core.prepare("root@203.0.113.9", "root-pw-123", lines.append))
        log = open(self.log, encoding="utf-8").read()
        self.assertTrue(os.path.exists(core.ssh_key_path() + ".pub"))
        self.assertIn("cat > /tmp/wa-bootstrap.sh", log)
        self.assertIn("bash /tmp/wa-bootstrap.sh", log)
        self.assertIn("IN: #!/usr/bin/env bash", log)                # se subió el bootstrap
        self.assertNotIn("root-pw-123", log + "\n".join(lines))
        for f in os.listdir(tempfile.gettempdir()):                  # el script askpass se borra
            self.assertFalse(f.startswith("wa-ask-") and os.path.exists(os.path.join(tempfile.gettempdir(), f)), f)


class Panel(unittest.TestCase):
    def setUp(self):
        reset_files()

    def test_auth_headers_and_csp(self):
        self.assertEqual(http("/api/state", token="bad")[0], 401)
        self.assertEqual(http("/api/state", headers={"Host": "evil.com"})[0], 403)
        self.assertEqual(http("/api/vps", {"ip": "1.2.3.4"}, headers={"Origin": "http://evil.com"})[0], 403)
        self.assertEqual(http("/agent/state", ui=True)[0], 401)       # el token del panel no vale para /agent
        self.assertEqual(http("/api/state", ui=False)[0], 401)        # y el del agente no vale para el panel
        self.assertEqual(http("/api/vps", {"ip": "1.2.3.4"}, ui=False)[0], 403)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(f"http://127.0.0.1:{SERVER.port}/?t=wrong")
        self.assertEqual(cm.exception.code, 403)
        r = urllib.request.urlopen(f"http://127.0.0.1:{SERVER.port}/?t={SERVER.ui_token}")
        self.assertEqual(r.status, 200)
        csp = r.headers["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("unsafe-inline", csp)
        html = r.read().decode()
        self.assertNotIn(" style=", html)
        self.assertIsNone(re.search(r"<script(?![^>]*src=)[^>]*>", html))   # sin scripts en línea
        for f in ("app.js", "app.css", "icons.js"):
            self.assertEqual(urllib.request.urlopen(f"http://127.0.0.1:{SERVER.port}/static/{f}").status, 200)
        js = open(os.path.join(REPO, "wa_proxy", "static", "app.js"), encoding="utf-8").read()
        self.assertNotIn("innerHTML", js)                              # nada de HTML con datos del servidor
        if os.path.exists(dashboard.SESSION_FILE) and not core.IS_WIN:
            self.assertEqual(stat.S_IMODE(os.stat(dashboard.SESSION_FILE).st_mode), 0o600)

    def test_ui_accounts_never_return_password(self):
        code, _ = http("/api/accounts", {"accounts": [{"n": None, "label": "V", "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1"}]})
        self.assertEqual(code, 200)
        self.assertNotIn("p@ss", json.dumps(http("/api/state")[1]))
        self.assertNotIn("p@ss", json.dumps(http("/agent/state", ui=False)[1]))

    @unittest.skipUnless(internet(), "sin internet")
    def test_agent_verify_runs_without_approval(self):
        http("/api/accounts", {"accounts": [{"n": None, "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1"}]})
        p = wa_agent("run", "verify")
        out, _ = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 0, out)
        self.assertIn("[OK]", out)
        self.assertNotIn("p@ss", out)

    def test_agent_asks_proxy_credentials(self):
        p = wa_agent("ask-proxy", "--n", "1", "--label", "Ventas", "--message", "Necesito el proxy")
        req = wait_pending("proxy")
        self.assertEqual(req["params"]["label"], "Ventas")
        code, _ = http(f"/api/requests/{req['id']}/answer", {"decision": "submit", "host": "bad host", "port": 1, "user": "u", "password": "pppp"})
        self.assertEqual(code, 400)                                    # datos inválidos: sigue pendiente
        self.assertEqual(wait_pending("proxy")["id"], req["id"])
        code, _ = http(f"/api/requests/{req['id']}/answer", {"decision": "submit", "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1", "label": "Ventas"})
        self.assertEqual(code, 200)
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 0, out)
        self.assertNotIn("p@ss", out)                                  # el agente nunca ve la contraseña
        self.assertIn("p%40ss%3Aw%2Frd%231", open(core.ENV_FILE, encoding="utf-8").read())
        kinds = [e["key"] for e in dashboard.HUB.events]
        self.assertIn("req_proxy", kinds)
        self.assertIn("proxy_saved", kinds)
        self.assertNotIn("p@ss", json.dumps(dashboard.HUB.events))

    def test_agent_ask_vps_and_denial(self):
        p = wa_agent("ask-vps")
        req = wait_pending("vps")
        http(f"/api/requests/{req['id']}/answer", {"decision": "submit", "ip": "203.0.113.50", "alias": "mi-vps"})
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 0, out)
        self.assertIn("mi-vps", out)
        p = wa_agent("confirm", "¿Seguimos?")
        req = wait_pending("confirm")
        http(f"/api/requests/{req['id']}/answer", {"decision": "deny"})
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 1, out)

    def test_actions_need_user_approval(self):
        core.add_vps({"ip": "203.0.113.9"})
        p = wa_agent("run", "deploy", "--alias", "vps1")
        req = wait_pending("approve")
        self.assertEqual(req["params"]["action"], "deploy")
        self.assertFalse(any(j.kind == "deploy" for j in dashboard.HUB.jobs.values()), "no debe ejecutarse antes de aprobar")
        http(f"/api/requests/{req['id']}/answer", {"decision": "deny"})
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 1, out)
        self.assertFalse(any(j.kind == "deploy" for j in dashboard.HUB.jobs.values()))
        # valores peligrosos se rechazan antes de pedir nada
        self.assertEqual(http("/agent/run", {"action": "power", "alias": "vps1", "n": "1;ls", "do": "stop"}, ui=False)[0], 400)
        self.assertEqual(http("/agent/run", {"action": "power", "alias": "vps1", "n": 1, "do": "rm"}, ui=False)[0], 400)
        self.assertEqual(http("/agent/run", {"action": "bash", "alias": "vps1"}, ui=False)[0], 400)
        self.assertEqual(http("/agent/run", {"action": "deploy", "alias": "nadie"}, ui=False)[0], 404)

    def test_approved_action_runs_job(self):
        reset_files()
        os.environ["WA_SSH_EXTRA"] = "-o ConnectTimeout=1"
        core.add_vps({"ip": "127.0.0.1"})
        p = wa_agent("run", "power", "--alias", "vps1", "--n", "1", "--do", "stop")
        req = wait_pending("approve")
        http(f"/api/requests/{req['id']}/answer", {"decision": "submit"})
        out, _ = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 1, out)                         # no hay ssh útil: el trabajo falla, pero SE EJECUTÓ
        self.assertTrue(any(j.kind == "power" for j in dashboard.HUB.jobs.values()))
        os.environ.pop("WA_SSH_EXTRA", None)

    def test_timeout_and_no_panel(self):
        p = wa_agent("confirm", "--timeout", "1", "¿Hola?")
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 2, out)
        self.assertEqual(dashboard.HUB.pending_requests(), [])         # se cancela al agotar el tiempo
        saved = open(dashboard.SESSION_FILE, encoding="utf-8").read()
        os.remove(dashboard.SESSION_FILE)
        try:
            p = wa_agent("say", "hola")
            out, _ = p.communicate(timeout=30)
            self.assertEqual(p.returncode, 3, out)
        finally:
            open(dashboard.SESSION_FILE, "w", encoding="utf-8").write(saved)

    def test_say_working_feed(self):
        self.assertEqual(wa_agent("say", "Probando", "el", "panel").wait(timeout=30), 0)
        self.assertEqual(wa_agent("working", "Revisando", "proxies").wait(timeout=30), 0)
        code, f = http("/api/feed?since=0")
        self.assertEqual(code, 200)
        self.assertTrue(any(e["text"] == "Probando el panel" for e in f["events"]))
        self.assertEqual(f["agent"]["working"], "Revisando proxies")
        self.assertEqual(wa_agent("working", "--done").wait(timeout=30), 0)
        self.assertEqual(http("/api/feed?since=0")[1]["agent"]["working"], "")


class Launchers(unittest.TestCase):
    def test_cli_help_and_doctor(self):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, os.path.join(REPO, "wa.py"), "--help"], capture_output=True, text=True, env=env, encoding="utf-8")
        self.assertEqual(r.returncode, 0)
        self.assertIn("dashboard", r.stdout)
        reset_files()
        r = subprocess.run([sys.executable, os.path.join(REPO, "wa.py"), "doctor"], capture_output=True, text=True, env=env, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("falta .env", r.stdout)

    def test_files_have_expected_line_endings(self):
        for f in ("wa.cmd", "start-dashboard.cmd"):
            data = open(os.path.join(REPO, f), "rb").read()
            self.assertIn(b"\r\n", data, f)
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""), f"{f} tiene saltos de línea sin CR")
        for f in ("wa", os.path.join("scripts", "bootstrap-vps.sh")):
            self.assertNotIn(b"\r", open(os.path.join(REPO, f), "rb").read(), f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
