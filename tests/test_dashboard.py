#!/usr/bin/env python3
"""Pruebas del dashboard. Se ejecutan sobre una COPIA del repo (ver smoke.sh)."""
import json, os, re, socket, subprocess, sys, time, unittest, urllib.error, urllib.request

ROOT = os.environ["WA_TEST_ROOT"]
PORT = 18900
B = f"http://127.0.0.1:{PORT}"
SOCKS = [(19101, "usr", "p@ss:w/rd#1"), (19102, "usr2", "x")]
procs, TOK = [], ""


def call(path, body=None, tok=None, headers=None):
    h = {"X-Token": TOK if tok is None else tok, "Content-Type": "application/json", **(headers or {})}
    r = urllib.request.Request(B + path, data=None if body is None else json.dumps(body).encode(),
                               headers=h, method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(r) as x:
            return x.status, json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def job(path, body):
    _, r = call(path, body)
    jid = r["job"]
    for _ in range(60):
        time.sleep(1)
        _, j = call(f"/api/jobs/{jid}")
        if j["status"] != "running":
            return j
    raise TimeoutError


def internet():
    try:
        socket.create_connection(("api.ipify.org", 443), timeout=5).close()
        return True
    except OSError:
        return False


def setUpModule():
    global TOK
    for port, u, p in SOCKS:
        procs.append(subprocess.Popen([sys.executable, os.path.join(ROOT, "tests/fake_socks5.py"), str(port), u, p]))
    env = {**os.environ, "WA_SSH_KEY": os.path.join(ROOT, "tests/.nokey")}
    srv = subprocess.Popen([sys.executable, "-u", os.path.join(ROOT, "dashboard/server.py"), "--port", str(PORT)],
                           stdout=subprocess.PIPE, text=True, env=env)
    procs.append(srv)
    for _ in range(50):
        line = srv.stdout.readline()
        m = re.search(r"t=(\S+)", line)
        if m:
            TOK = m.group(1)
            break
    time.sleep(0.5)


def tearDownModule():
    for p in procs:
        p.terminate()


class Dashboard(unittest.TestCase):
    def test_1_auth(self):
        self.assertEqual(call("/api/state", tok="bad")[0], 401)
        self.assertEqual(call("/api/state", headers={"Host": "evil.com"})[0], 403)
        self.assertEqual(call("/api/vps", {"ip": "1.2.3.4"}, headers={"Origin": "http://evil.com"})[0], 403)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(B + "/?t=wrong")
        self.assertEqual(cm.exception.code, 403)
        self.assertEqual(urllib.request.urlopen(B + "/?t=" + TOK).status, 200)

    def test_2_accounts(self):
        accs = [{"n": None, "label": 'Ventas "x" $(rm)', "host": "127.0.0.1", "port": 19101, "user": "usr", "password": "p@ss:w/rd#1"},
                {"n": None, "label": "", "host": "127.0.0.1", "port": "19102", "user": "usr2", "password": "x"}]
        code, r = call("/api/accounts", {"accounts": accs})
        self.assertEqual(code, 200)
        env_path = os.path.join(ROOT, ".env")
        self.assertEqual(oct(os.stat(env_path).st_mode & 0o777), "0o600")
        txt = open(env_path).read()
        self.assertIn('PROXY_1="socks5://usr:p%40ss%3Aw%2Frd%231@127.0.0.1:19101"', txt)
        self.assertNotIn("$(", txt)
        self.assertNotIn("p@ss", json.dumps(call("/api/state")[1]))   # nunca devuelve la clave
        cur = call("/api/state")[1]["accounts"]
        cur[0]["password"] = ""                                       # vacía = conservar
        self.assertEqual(call("/api/accounts", {"accounts": cur})[0], 200)
        self.assertIn("p%40ss%3Aw%2Frd%231", open(env_path).read())
        self.assertEqual(call("/api/accounts", {"accounts": [{"n": 1, "host": "a b;rm", "port": 1, "user": "u", "password": "p"}]})[0], 400)
        self.assertEqual(call("/api/accounts", {"accounts": [{"n": None, "host": "h.com", "port": 1, "user": "u"}]})[0], 400)

    def test_3_verify(self):
        if not internet():
            self.skipTest("sin internet")
        j = job("/api/verify", {})
        res = j["result"]
        self.assertEqual(len(res["accounts"]), 2)
        for a in res["accounts"]:
            self.assertTrue(a["exit_ip"], a)
            self.assertTrue(all(t["ok"] for t in a["targets"]), a)
        self.assertTrue(res["duplicate_ips"])    # ambos SOCKS de prueba salen por la misma IP

    def test_4_vps(self):
        self.assertEqual(call("/api/vps", {"ip": "203.0.113.9"})[0], 200)
        self.assertEqual(call("/api/vps", {"ip": "1.2.3.4; rm -rf /"})[0], 400)
        self.assertIn("vps1=wa@203.0.113.9", open(os.path.join(ROOT, "hosts.conf")).read())
        self.assertEqual(call("/api/power", {"alias": "vps1", "n": 1, "action": "rm -rf"})[0], 400)
        self.assertEqual(call("/api/power", {"alias": "vps1", "n": "1;ls", "action": "stop"})[0], 400)

    def test_5_partial_gateway(self):
        """Un proxy que solo responde por una de las IPs de su pasarela debe marcarse como parcial."""
        if not internet():
            self.skipTest("sin internet")
        sys.path.insert(0, os.path.join(ROOT, "dashboard"))
        import server
        acc = {"n": 1, "label": "", "host": "127.0.0.1", "port": SOCKS[0][0],
               "enc_user": "usr", "enc_pass": "p%40ss%3Aw%2Frd%231"}
        server.resolve_gateways = lambda h: ["127.0.0.1", "127.0.0.2"]   # 127.0.0.2: nadie escucha
        r = server.check_account(acc, "api.ipify.org")
        self.assertTrue(r["partial"], r)
        self.assertEqual([g["ok"] for g in r["gateways"]], [True, False])
        self.assertTrue(r["exit_ip"])
        server.resolve_gateways = lambda h: ["127.0.0.1"]
        r = server.check_account(acc, "api.ipify.org")
        self.assertFalse(r["partial"])
        self.assertEqual(r["gateways"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
