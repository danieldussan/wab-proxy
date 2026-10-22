"""Panel local + canal del agente.

- Escucha SOLO en 127.0.0.1. Dos tokens distintos:
    * token del PANEL (va en el enlace que abre el usuario; solo vive en memoria)
    * token del AGENTE (archivo .wa-session.json, permisos 600)
- Nunca devuelve contraseñas; la salida de los trabajos se limpia de secretos.
- Solo ejecuta una lista fija de acciones (no hay "ejecutar comando").
- El agente NO puede preparar/desplegar/encender/apagar sin que el usuario lo apruebe en el panel.
"""
import hmac, http.server, json, mimetypes, os, re, secrets, shutil, subprocess, sys, threading, time
import urllib.parse, webbrowser

from . import core
from .core import ApiError

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
SESSION_FILE = os.path.join(core.ROOT, ".wa-session.json")
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
ACTIONS = ("verify", "prepare", "deploy", "power")


class Job:
    def __init__(self, kind, alias="", who="user"):
        self.id = secrets.token_hex(6)
        self.kind, self.alias, self.who = kind, alias, who
        self.status, self.lines, self.result = "running", [], None
        self.started = time.time()
        self.lock = threading.Lock()

    def add(self, line):
        with self.lock:
            self.lines.append(line)
            if len(self.lines) > 4000:
                del self.lines[:1000]

    def finish(self, ok, result=None):
        with self.lock:
            self.status = "ok" if ok else "fail"
            self.result = result


class Hub:
    """Estado compartido en memoria: eventos, solicitudes, trabajos."""

    def __init__(self):
        self.cv = threading.Condition()
        self.events, self.next_id = [], 1
        self.requests, self.jobs = {}, {}
        self.agent_seen, self.agent_working = 0.0, ""
        self.version = 1
        self.last_verify = None
        self.closing = False

    def bump(self):
        with self.cv:
            self.version += 1
            self.cv.notify_all()

    def event(self, who, level="info", key=None, params=None, text=None):
        with self.cv:
            self.events.append({"id": self.next_id, "ts": time.time(), "who": who, "level": level,
                                "key": key, "params": params or {}, "text": text})
            self.next_id += 1
            del self.events[:-300]
            self.cv.notify_all()

    def new_job(self, kind, alias, who, target):
        job = Job(kind, alias, who)
        with self.cv:
            if any(j.kind == kind and j.status == "running" for j in self.jobs.values()):
                raise ApiError("Ya hay una operación igual en curso. Espera a que termine.", 409)
            for jid in [k for k, j in self.jobs.items() if j.status != "running"][:-20]:
                self.jobs.pop(jid, None)
            self.jobs[job.id] = job
        self.event(who, "info", "job_start", {"kind": job.kind, "alias": alias, "job": job.id})
        self.bump()

        def runner():
            try:
                target(job)
            except ApiError as e:
                job.add(str(e))
                job.finish(False)
            except Exception as e:                          # noqa: BLE001
                job.add(f"Error inesperado: {e}")
                job.finish(False)
            self.event(who, "ok" if job.status == "ok" else "er",
                       "job_ok" if job.status == "ok" else "job_fail", {"kind": kind, "alias": alias, "job": job.id})
            self.bump()
        threading.Thread(target=runner, daemon=True).start()
        return job.id

    def latest_job(self):
        with self.cv:
            jobs = sorted(self.jobs.values(), key=lambda j: j.started)
        run = [j for j in jobs if j.status == "running"]
        j = (run or jobs or [None])[-1]
        return None if not j else {"id": j.id, "kind": j.kind, "alias": j.alias, "status": j.status, "who": j.who}

    def pending_requests(self):
        with self.cv:
            return [r for r in self.requests.values() if r["status"] == "pending"]


HUB = Hub()


# ----------------------------------------------------------------- acciones (compartidas por el panel y el agente)

def start_action(action, data, who):
    """Valida y lanza una acción como trabajo. -> id del trabajo."""
    if action == "verify":
        def t(job):
            ok, res = core.verify_accounts(job.add)
            if res is not None:
                HUB.last_verify = {"ts": time.time(), "result": res}
                for line in core.format_verify(res):
                    job.add(line)
            job.finish(ok, res)
        return HUB.new_job("verify", "", who, t)
    host = core.find_host(str(data.get("alias", "")))
    if action == "prepare":
        initial = str(data.get("initial_user") or "root").strip()
        if not core.RE_USER.match(initial):
            raise ApiError("Usuario inicial inválido")
        password = data.get("password") or ""
        dest = f"{initial}@{core.valid_ip_or_host(host['ip'])}"
        return HUB.new_job("prepare", host["alias"], who, lambda job: job.finish(core.prepare(dest, password, job.add)))
    if action == "deploy":
        return HUB.new_job("deploy", host["alias"], who,
                           lambda job: job.finish(core.deploy(host["alias"], True, bool(data.get("pull")), True, job.add)))
    if action == "power":
        n, do = data.get("n"), data.get("do")
        if do not in ("start", "stop", "restart"):
            raise ApiError("Acción inválida")
        try:
            assert 1 <= int(n) <= 99
        except Exception:
            raise ApiError("Cuenta inválida")
        return HUB.new_job("power", host["alias"], who, lambda job: job.finish(core.power(host, n, do, job.add)))
    raise ApiError("Acción desconocida")


def short(s, n=300):
    return re.sub(r"[\x00-\x1f]", " ", str(s or "")).strip()[:n]


def create_request(kind, params):
    rid = secrets.token_hex(6)
    req = {"id": rid, "kind": kind, "status": "pending", "created": time.time(), "params": params, "result": None}
    with HUB.cv:
        HUB.requests[rid] = req
    HUB.event("agent", "req", "req_" + kind, dict(params, req=rid))
    HUB.bump()
    return req


def settle(req, status, result=None):
    with HUB.cv:
        req["status"], req["result"] = status, result
        HUB.cv.notify_all()
    HUB.bump()


def answer_request(rid, body):
    req = HUB.requests.get(rid)
    if not req or req["status"] != "pending":
        raise ApiError("La solicitud ya no está pendiente", 404)
    if body.get("decision") != "submit":
        HUB.event("user", "info", "req_denied", {"kind": req["kind"], **{k: v for k, v in req["params"].items() if k in ("action", "alias", "n")}})
        return settle(req, "denied")
    kind, p = req["kind"], req["params"]
    if kind == "proxy":
        n, _ = core.upsert_account({"n": p.get("n") or body.get("n"), "label": body.get("label"), "host": body.get("host"),
                                    "port": body.get("port"), "user": body.get("user"), "password": body.get("password")})
        label = core.clean_text(body.get("label"))
        HUB.event("user", "ok", "proxy_saved", {"n": n, "label": label})
        settle(req, "done", {"saved": True, "n": n})
    elif kind == "vps":
        hosts = core.add_vps({"ip": body.get("ip"), "alias": body.get("alias")})
        h = next(x for x in hosts if x["ip"] == str(body.get("ip")).strip())
        HUB.event("user", "ok", "vps_saved", {"alias": h["alias"], "ip": h["ip"]})
        settle(req, "done", {"saved": True, "alias": h["alias"]})
    elif kind == "confirm":
        HUB.event("user", "ok", "req_confirmed", {})
        settle(req, "done", {"approved": True})
    elif kind == "approve":
        data = dict(p)
        if p["action"] == "prepare":
            data.update(initial_user=body.get("initial_user"), password=body.get("password") or "")
        job = start_action(p["action"], data, "agent")
        HUB.event("user", "ok", "approved", {"action": p["action"], "alias": p.get("alias", ""), "n": p.get("n"), "do": p.get("do")})
        settle(req, "done", {"job": job})
    HUB.bump()


# ----------------------------------------------------------------- sesión del agente

def write_session(port, agent_token):
    core.write_private(SESSION_FILE, json.dumps({"port": port, "agent_token": agent_token, "pid": os.getpid()}))


def remove_session():
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            if json.load(f).get("pid") != os.getpid():
                return
        os.remove(SESSION_FILE)
    except (OSError, ValueError):
        pass


# ----------------------------------------------------------------- HTTP

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "wa-panel"

    def log_message(self, *a):
        pass

    @property
    def S(self):
        return self.server

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith(("text", "application/json", "application/javascript")) else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", CSP)
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{self.S.port}", f"localhost:{self.S.port}")

    def _origin_ok(self):
        o = self.headers.get("Origin")
        return o is None or o in (f"http://127.0.0.1:{self.S.port}", f"http://localhost:{self.S.port}")

    def _ui(self):
        return hmac.compare_digest(self.headers.get("X-Token", ""), self.S.ui_token)

    def _agent(self):
        return hmac.compare_digest(self.headers.get("X-Agent-Token", ""), self.S.agent_token)

    def _static(self, name):
        files = {"": "index.html", "app.js": "app.js", "app.css": "app.css", "icons.js": "icons.js"}
        if name not in files:
            return self._send(404, {"error": "no encontrado"})
        with open(os.path.join(STATIC, files[name]), "rb") as f:
            self._send(200, f.read(), {"js": "application/javascript", "css": "text/css", "html": "text/html"}[files[name].rsplit(".", 1)[1]])

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        u = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/":
                if not hmac.compare_digest(q.get("t", [""])[0], self.S.ui_token):
                    return self._send(403, "Abre el enlace completo (incluye ?t=...). Si lo perdiste, ejecuta `wa dashboard` otra vez.".encode(), "text/plain")
                return self._static("")
            if u.path.startswith("/static/"):
                return self._static(u.path[8:])
            if u.path.startswith("/agent/"):
                if not self._agent():
                    return self._send(401, {"error": "token"})
                HUB.agent_seen = time.time()
                return self._agent_get(u.path, q)
            if not self._ui():
                return self._send(401, {"error": "token"})
            return self._ui_get(u.path, q)
        except ApiError as e:
            self._send(e.code, {"error": str(e)})

    def _job_json(self, jid, q):
        job = HUB.jobs.get(jid)
        if not job:
            raise ApiError("Trabajo no encontrado", 404)
        since = int(q.get("since", ["0"])[0])
        with job.lock:
            return {"status": job.status, "lines": job.lines[since:], "next": len(job.lines),
                    "result": job.result, "kind": job.kind, "alias": job.alias}

    def _ui_get(self, path, q):
        if path == "/api/state":
            _, probe, _ = core.read_env()
            return self._send(200, {"accounts": core.public_accounts(), "vps": core.read_hosts(), "probe_host": probe,
                                    "tools": core.tool_checks(), "ssh_key": os.path.exists(core.ssh_key_path() + ".pub"),
                                    "env_exists": os.path.exists(core.ENV_FILE), "last_verify": HUB.last_verify,
                                    "version": HUB.version})
        if path == "/api/feed":
            since = int(q.get("since", ["0"])[0])
            with HUB.cv:
                evs = [e for e in HUB.events if e["id"] > since]
                ago = time.time() - HUB.agent_seen if HUB.agent_seen else None
            return self._send(200, {"events": evs, "requests": HUB.pending_requests(), "version": HUB.version,
                                    "agent": {"ago": ago, "working": HUB.agent_working}, "job": HUB.latest_job()})
        m = re.match(r"^/api/jobs/([0-9a-f]+)$", path)
        if m:
            return self._send(200, self._job_json(m.group(1), q))
        raise ApiError("No encontrado", 404)

    def _agent_get(self, path, q):
        if path == "/agent/ping":
            return self._send(200, {"ok": True})
        if path == "/agent/state":
            _, probe, _ = core.read_env()
            lv = HUB.last_verify
            return self._send(200, {"accounts": core.public_accounts(), "vps": core.read_hosts(), "probe_host": probe,
                                    "env_exists": os.path.exists(core.ENV_FILE),
                                    "last_verify": None if not lv else {"ts": lv["ts"], "ok": all(core.account_ok(r) for r in lv["result"]["accounts"]) and not lv["result"]["duplicate_ips"],
                                                                         "accounts": [{"n": r["n"], "exit_ip": r["exit_ip"], "ok": core.account_ok(r)} for r in lv["result"]["accounts"]]},
                                    "pending": [{"id": r["id"], "kind": r["kind"]} for r in HUB.pending_requests()]})
        m = re.match(r"^/agent/request/([0-9a-f]+)$", path)
        if m:
            req = HUB.requests.get(m.group(1))
            if not req:
                raise ApiError("Solicitud no encontrada", 404)
            wait = min(int(q.get("wait", ["0"])[0]), 25)
            end = time.time() + wait
            with HUB.cv:
                while req["status"] == "pending" and not HUB.closing and time.time() < end:
                    HUB.cv.wait(timeout=max(0.1, end - time.time()))
            return self._send(200, {"status": req["status"], "result": req["result"]})
        m = re.match(r"^/agent/jobs/([0-9a-f]+)$", path)
        if m:
            j = self._job_json(m.group(1), q)
            if j["kind"] == "verify" and j["result"]:      # al agente solo un resumen, sin datos de pasarelas
                j["result"] = {"accounts": [{"n": r["n"], "exit_ip": r["exit_ip"], "ok": core.account_ok(r), "partial": r["partial"],
                                              "inconsistent_ip": r["inconsistent_ip"], "error": r["error"]} for r in j["result"]["accounts"]],
                               "duplicate_ips": j["result"]["duplicate_ips"]}
            return self._send(200, j)
        raise ApiError("No encontrado", 404)

    def do_POST(self):
        if not (self._host_ok() and self._origin_ok()):
            return self._send(403, {"error": "forbidden"})
        p = urllib.parse.urlsplit(self.path).path
        is_agent = p.startswith("/agent/")
        if not (self._agent() if is_agent else self._ui()):
            return self._send(403, {"error": "forbidden"})
        if is_agent:
            HUB.agent_seen = time.time()
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 100_000:
                raise ApiError("Petición demasiado grande", 413)
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ApiError("Formato inválido")
            return self._agent_post(p, data) if is_agent else self._ui_post(p, data)
        except ApiError as e:
            self._send(e.code, {"error": str(e)})
        except (KeyError, ValueError, json.JSONDecodeError):
            self._send(400, {"error": "Datos inválidos"})

    def _ui_post(self, p, data):
        if p == "/api/accounts":
            r = core.save_accounts(data.get("accounts"))
            HUB.event("user", "info", "accounts_saved", {})
            HUB.last_verify = None
            HUB.bump()
            return self._send(200, {"accounts": r})
        if p == "/api/vps":
            r = core.add_vps(data)
            HUB.event("user", "info", "vps_added", {"ip": str(data.get("ip", "")).strip()})
            HUB.bump()
            return self._send(200, {"vps": r})
        if p == "/api/vps/delete":
            r = core.delete_vps(str(data.get("alias", "")))
            HUB.bump()
            return self._send(200, {"vps": r})
        if p == "/api/ssh-key":
            return self._send(200, {"public_key": core.ensure_key()})
        if p in ("/api/verify", "/api/prepare", "/api/deploy", "/api/power"):
            return self._send(200, {"job": start_action(p[5:], data, "user")})
        if p == "/api/status":
            host = core.find_host(str(data.get("alias", "")))
            return self._send(200, core.vps_status(host))
        m = re.match(r"^/api/requests/([0-9a-f]+)/answer$", p)
        if m:
            answer_request(m.group(1), data)
            return self._send(200, {"ok": True})
        if p == "/api/quit":
            self._send(200, {"ok": True})
            threading.Thread(target=self.S.stop, daemon=True).start()
            return
        raise ApiError("No encontrado", 404)

    def _agent_post(self, p, data):
        if p == "/agent/say":
            text = short(data.get("text"), 500)
            if text:
                HUB.event("agent", "info", None, None, text)
            return self._send(200, {"ok": True})
        if p == "/agent/working":
            HUB.agent_working = short(data.get("text"), 120)
            HUB.bump()
            return self._send(200, {"ok": True})
        if p == "/agent/open":
            threading.Thread(target=lambda: webbrowser.open(self.S.url()), daemon=True).start()
            return self._send(200, {"ok": True})
        if p == "/agent/request":
            kind = data.get("kind")
            if kind == "proxy":
                n = data.get("n")
                params = {"message": short(data.get("message")), "label": core.clean_text(data.get("label")),
                          "n": int(n) if str(n or "").isdigit() else None}
            elif kind == "vps":
                params = {"message": short(data.get("message"))}
            elif kind == "confirm":
                params = {"message": short(data.get("message"))}
                if not params["message"]:
                    raise ApiError("Falta el mensaje")
            else:
                raise ApiError("Tipo de solicitud inválido")
            return self._send(200, {"request": create_request(kind, params)["id"]})
        if p == "/agent/run":
            action = data.get("action")
            if action not in ACTIONS:
                raise ApiError("Acción inválida")
            if action == "verify":
                return self._send(200, {"job": start_action("verify", {}, "agent")})
            host = core.find_host(str(data.get("alias", "")))
            params = {"action": action, "alias": host["alias"], "ip": host["ip"], "message": short(data.get("message"))}
            if action == "power":
                if data.get("do") not in ("start", "stop", "restart"):
                    raise ApiError("Acción inválida (start, stop o restart)")
                try:
                    params["n"] = int(data.get("n"))
                    assert 1 <= params["n"] <= 99
                except Exception:
                    raise ApiError("Cuenta inválida")
                params["do"] = data["do"]
            return self._send(200, {"request": create_request("approve", params)["id"]})
        m = re.match(r"^/agent/request/([0-9a-f]+)/cancel$", p)
        if m:
            req = HUB.requests.get(m.group(1))
            if req and req["status"] == "pending":
                settle(req, "cancelled")
            return self._send(200, {"ok": True})
        if p == "/agent/status":
            host = core.find_host(str(data.get("alias", "")))
            return self._send(200, core.vps_status(host))
        raise ApiError("No encontrado", 404)


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, ui_token, agent_token):
        super().__init__(("127.0.0.1", port), Handler)
        self.port, self.ui_token, self.agent_token = port, ui_token, agent_token

    def url(self):
        return f"http://127.0.0.1:{self.port}/?t={self.ui_token}"

    def stop(self):
        HUB.closing = True
        for r in HUB.pending_requests():
            settle(r, "cancelled")
        self.shutdown()


def serve(port=8787, open_browser=False, quiet=False):
    srv = None
    for pt in range(port, port + 20):
        try:
            srv = Server(pt, secrets.token_urlsafe(24), secrets.token_urlsafe(24))
            break
        except OSError:
            continue
    if not srv:
        raise SystemExit("No encontré un puerto libre.")
    write_session(srv.port, srv.agent_token)
    if not quiet:
        print(f"\nPanel listo. Abre este enlace en tu navegador:\n\n  {srv.url()}\n\n(Ctrl+C para cerrar)", flush=True)
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(srv.url())).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        remove_session()
