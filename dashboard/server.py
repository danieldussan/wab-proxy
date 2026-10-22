#!/usr/bin/env python3
"""Panel local para configurar y vigilar los proxies de WhatsApp.

- Solo librería estándar de Python 3.8+. Sin dependencias.
- Escucha SOLO en 127.0.0.1 y exige un token aleatorio (se imprime al arrancar).
- Nunca devuelve contraseñas al navegador; la salida de los trabajos se limpia de secretos.
- Solo ejecuta una lista fija de acciones (no hay "ejecutar comando").

Uso:  python3 dashboard/server.py [--open] [--port 8787]
"""
import argparse, hmac, http.server, ipaddress, json, os, re, secrets, shutil, socket
import shlex, ssl, struct, subprocess, tempfile, threading, time, urllib.parse, webbrowser
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, ".env")
HOSTS_FILE = os.path.join(ROOT, "hosts.conf")
INDEX = os.path.join(ROOT, "dashboard", "index.html")
SSH_KEY = os.environ.get("WA_SSH_KEY", os.path.expanduser("~/.ssh/wa-proxy_ed25519"))
TARGETS = [("g.whatsapp.net", 5222), ("g.whatsapp.net", 443), ("whatsapp.net", 443)]
WA_USER = "wa"
REMOTE_DIR = "wa-proxy"

FILE_LOCK = threading.Lock()
TOKEN = secrets.token_urlsafe(24)
PORT = 8787
JOBS = {}
JOBS_LOCK = threading.Lock()

RE_HOST = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
RE_ALIAS = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
RE_USER = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


class ApiError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


# ----------------------------------------------------------------- .env / hosts

def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def read_env():
    """-> (accounts{n:{...,'enc_user','enc_pass'}}, probe_host, otras_lineas)"""
    accounts, probe, others = {}, "api.ipify.org", []
    if not os.path.exists(ENV_FILE):
        return accounts, probe, others
    with open(ENV_FILE, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = re.match(r"^(PROXY|LABEL)_(\d+)=(.*)$", line)
            if m:
                kind, n, val = m.group(1), int(m.group(2)), unquote(m.group(3))
                acc = accounts.setdefault(n, {"n": n, "label": ""})
                if kind == "LABEL":
                    acc["label"] = val
                elif val:
                    u = urllib.parse.urlsplit(val)
                    acc.update(host=u.hostname or "", port=u.port or 0,
                               enc_user=u.username or "", enc_pass=u.password or "")
                continue
            m = re.match(r"^PROBE_HOST=(.*)$", line)
            if m:
                probe = unquote(m.group(1)) or probe
                continue
            if line.strip() and not line.startswith("#"):
                others.append(line)
    accounts = {n: a for n, a in accounts.items() if a.get("host")}
    return accounts, probe, others


def write_env(accounts, probe, others):
    lines = ["# Generado por el panel (dashboard). Puedes editarlo a mano; NO lo compartas.",
             "# Cuenta N usa en la VPS: chat 5100+N, medios 5200+N, sonda 5300+N.", ""]
    for n in sorted(accounts):
        a = accounts[n]
        lines.append(f'PROXY_{n}="socks5://{a["enc_user"]}:{a["enc_pass"]}@{a["host"]}:{a["port"]}"')
        if a.get("label"):
            lines.append(f'LABEL_{n}="{a["label"]}"')
    lines += ["", f'PROBE_HOST="{probe}"'] + others
    tmp = ENV_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, ENV_FILE)
    os.chmod(ENV_FILE, 0o600)


def clean_text(s, maxlen=60):
    return re.sub(r'[\x00-\x1f"\'`$\\]', "", str(s or "")).strip()[:maxlen]


def public_accounts():
    accounts, _, _ = read_env()
    return [{"n": a["n"], "label": a["label"], "host": a["host"], "port": a["port"],
             "user": urllib.parse.unquote(a["enc_user"]), "has_password": bool(a["enc_pass"])}
            for _, a in sorted(accounts.items())]


def save_accounts(items):
    if not isinstance(items, list):
        raise ApiError("Formato inválido")
    with FILE_LOCK:
        old, probe, others = read_env()
        new = {}
        used = {int(i["n"]) for i in items if isinstance(i, dict) and str(i.get("n", "")).isdigit()}
        nxt = max(used | set(old) | {0}) + 1
        for it in items:
            if not isinstance(it, dict):
                raise ApiError("Formato inválido")
            n = int(it["n"]) if str(it.get("n", "")).isdigit() else None
            if n is None or n in new:
                n, nxt = nxt, nxt + 1
            if not 1 <= n <= 99:
                raise ApiError("Máximo 99 cuentas")
            host = str(it.get("host", "")).strip().lower()
            if not RE_HOST.match(host):
                raise ApiError(f"Cuenta {n}: servidor inválido (ej. isp.decodo.com)")
            try:
                port = int(it.get("port"))
                assert 1 <= port <= 65535
            except Exception:
                raise ApiError(f"Cuenta {n}: puerto inválido")
            user = str(it.get("user", ""))
            if not user or len(user) > 200 or re.search(r"[\x00-\x1f]", user):
                raise ApiError(f"Cuenta {n}: usuario inválido")
            pw = it.get("password")
            if pw:
                if len(pw) > 200 or re.search(r"[\x00-\x1f]", pw):
                    raise ApiError(f"Cuenta {n}: contraseña inválida")
                enc_pass = urllib.parse.quote(pw, safe="")
            elif n in old and old[n].get("enc_pass"):
                enc_pass = old[n]["enc_pass"]
            else:
                raise ApiError(f"Cuenta {n}: falta la contraseña")
            new[n] = {"n": n, "label": clean_text(it.get("label")), "host": host, "port": port,
                      "enc_user": urllib.parse.quote(user, safe=""), "enc_pass": enc_pass}
        write_env(new, probe, others)
    return public_accounts()


def read_hosts():
    out = []
    if os.path.exists(HOSTS_FILE):
        with open(HOSTS_FILE, encoding="utf-8") as f:
            for raw in f:
                line = raw.split("#", 1)[0].strip()
                if "=" in line:
                    alias, dest = line.split("=", 1)
                    user, _, ip = dest.rpartition("@")
                    out.append({"alias": alias.strip(), "user": user or WA_USER, "ip": ip.strip()})
    return out


def write_hosts(hosts):
    body = ["# Generado por el panel. Formato: alias=usuario@ip"]
    body += [f'{h["alias"]}={h["user"]}@{h["ip"]}' for h in hosts]
    tmp = HOSTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    os.replace(tmp, HOSTS_FILE)


def valid_ip_or_host(v):
    v = str(v or "").strip()
    try:
        ipaddress.ip_address(v)
        return v
    except ValueError:
        pass
    if RE_HOST.match(v):
        return v
    raise ApiError("IP o dominio de la VPS inválido")


def add_vps(data):
    ip = valid_ip_or_host(data.get("ip"))
    with FILE_LOCK:
        hosts = read_hosts()
        if any(h["ip"] == ip for h in hosts):
            raise ApiError("Esa VPS ya está en la lista")
        alias = clean_text(data.get("alias"), 32).replace(" ", "-")
        if not alias:
            i = 1
            while any(h["alias"] == f"vps{i}" for h in hosts):
                i += 1
            alias = f"vps{i}"
        if not RE_ALIAS.match(alias) or any(h["alias"] == alias for h in hosts):
            raise ApiError("Nombre inválido o repetido (usa letras, números, - y _)")
        hosts.append({"alias": alias, "user": WA_USER, "ip": ip})
        write_hosts(hosts)
    return read_hosts()


def delete_vps(alias):
    with FILE_LOCK:
        hosts = [h for h in read_hosts() if h["alias"] != alias]
        write_hosts(hosts)
    return hosts


def find_host(alias):
    for h in read_hosts():
        if h["alias"] == alias:
            return h
    raise ApiError("VPS no encontrada", 404)


# ----------------------------------------------------------------- secretos / jobs

def secret_values():
    vals = set()
    accounts, _, _ = read_env()
    for a in accounts.values():
        for v in (a.get("enc_pass", ""), urllib.parse.unquote(a.get("enc_pass", ""))):
            if len(v) >= 4:
                vals.add(v)
    return vals


def scrubber(extra=()):
    vals = sorted(secret_values() | {e for e in extra if e and len(e) >= 4}, key=len, reverse=True)

    def scrub(text):
        for v in vals:
            text = text.replace(v, "***")
        return re.sub(r"(://)[^@/\s]*@", r"\1***@", text)
    return scrub


class Job:
    def __init__(self, kind):
        self.id = secrets.token_hex(6)
        self.kind, self.status, self.lines, self.result = kind, "running", [], None
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


def new_job(kind, target):
    job = Job(kind)
    with JOBS_LOCK:
        for jid in [k for k, j in JOBS.items() if j.status != "running"][:-20]:
            JOBS.pop(jid, None)
        if any(j.kind == kind and j.status == "running" for j in JOBS.values()):
            raise ApiError("Ya hay una operación igual en curso. Espera a que termine.", 409)
        JOBS[job.id] = job
    threading.Thread(target=target, args=(job,), daemon=True).start()
    return job.id


def run_proc(job, argv, env=None, scrub=None):
    scrub = scrub or scrubber()
    penv = os.environ.copy()
    penv.update(env or {})
    penv["WA_BATCH"] = "1"
    try:
        p = subprocess.Popen(argv, cwd=ROOT, env=penv, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             errors="replace", start_new_session=True)
    except OSError as e:
        job.add(f"No se pudo ejecutar: {e}")
        return 127
    for line in p.stdout:
        job.add(scrub(line.rstrip("\n")))
    return p.wait()


def askpass_env(password):
    """Entorno para que ssh use la contraseña sin terminal (no se guarda en disco)."""
    d = tempfile.mkdtemp(prefix="wa-ask-")
    path = os.path.join(d, "ask.sh")
    with open(path, "w") as f:
        f.write('#!/bin/sh\nprintf "%s\\n" "$WA_ROOT_PASS"\n')
    os.chmod(path, 0o700)
    return d, {"SSH_ASKPASS": path, "SSH_ASKPASS_REQUIRE": "force", "DISPLAY": "wa:0",
               "WA_ROOT_PASS": password}


# ----------------------------------------------------------------- verificación de proxies (SOCKS5 puro)

def _rd(s, n):
    b = b""
    while len(b) < n:
        x = s.recv(n - len(b))
        if not x:
            raise OSError("conexión cerrada por el proxy")
        b += x
    return b


def socks5_connect(a, host, port, timeout=12, gateway=None):
    user = urllib.parse.unquote(a["enc_user"]).encode()
    pw = urllib.parse.unquote(a["enc_pass"]).encode()
    s = socket.create_connection((gateway or a["host"], a["port"]), timeout=timeout)
    try:
        s.sendall(b"\x05\x02\x00\x02")
        ver, method = _rd(s, 2)
        if method == 2:
            s.sendall(b"\x01" + bytes([len(user)]) + user + bytes([len(pw)]) + pw)
            if _rd(s, 2)[1] != 0:
                raise OSError("usuario o contraseña rechazados")
        elif method != 0:
            raise OSError("el proxy no acepta el método de autenticación")
        h = host.encode()
        s.sendall(b"\x05\x01\x00\x03" + bytes([len(h)]) + h + struct.pack(">H", port))
        rep = _rd(s, 4)
        if rep[1] != 0:
            raise OSError(f"el proxy no pudo conectar con {host}:{port} (código {rep[1]})")
        atyp = rep[3]
        _rd(s, {1: 4, 4: 16}.get(atyp) or (_rd(s, 1)[0]))
        _rd(s, 2)
        return s
    except Exception:
        s.close()
        raise


def resolve_gateways(host):
    """Todas las IPv4 detrás del nombre del proxy (el DNS puede rotar entre ellas)."""
    try:
        ips = sorted({r[4][0] for r in socket.getaddrinfo(host, None, socket.AF_INET)})
    except OSError:
        return []
    return ips or []


def check_gateway(a, probe_host, gateway):
    res = {"gateway": gateway, "exit_ip": None, "targets": [], "error": None}
    try:
        s = socks5_connect(a, probe_host, 443, gateway=gateway)
        t = ssl.create_default_context().wrap_socket(s, server_hostname=probe_host)
        t.settimeout(12)
        t.sendall(f"GET /?format=json HTTP/1.1\r\nHost: {probe_host}\r\nConnection: close\r\n\r\n".encode())
        buf = b""
        while True:
            c = t.recv(4096)
            if not c:
                break
            buf += c
        body = buf.decode(errors="replace")
        res["exit_ip"] = json.loads(body[body.index("{"):body.rindex("}") + 1])["ip"]
        t.close()
    except Exception as e:
        res["error"] = str(e) or e.__class__.__name__
    for host, port in TARGETS:
        ok = False
        if res["exit_ip"]:      # si la pasarela ni responde, no gastamos 10 s por destino
            try:
                socks5_connect(a, host, port, timeout=10, gateway=gateway).close()
                ok = True
            except Exception as e:
                res["error"] = res["error"] or str(e)
        res["targets"].append({"target": f"{host}:{port}", "ok": ok})
    res["ok"] = bool(res["exit_ip"]) and all(t["ok"] for t in res["targets"])
    return res


def check_account(a, probe_host):
    gws = resolve_gateways(a["host"]) or [a["host"]]
    with ThreadPoolExecutor(max_workers=len(gws)) as ex:
        gateways = list(ex.map(lambda g: check_gateway(a, probe_host, g), gws))
    good = [g for g in gateways if g["ok"]]
    shown = good[0] if good else gateways[0]
    return {
        "n": a["n"], "label": a.get("label", ""), "exit_ip": shown["exit_ip"], "targets": shown["targets"],
        "error": None if good and len(good) == len(gateways) else next((g["error"] for g in gateways if g["error"]), None),
        "gateways": gateways if len(gateways) > 1 else [],
        # funciona solo por algunas IPs: el DNS rota, así que fallaría de forma intermitente
        "partial": 0 < len(good) < len(gateways),
        "inconsistent_ip": len({g["exit_ip"] for g in good}) > 1,
    }


def job_verify(job):
    accounts, probe, _ = read_env()
    if not accounts:
        job.add("No hay proxies guardados.")
        return job.finish(False)
    job.add(f"Probando {len(accounts)} proxy(s)…")
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda a: check_account(a, probe), [accounts[n] for n in sorted(accounts)]))
    scrub = scrubber()
    for r in results:
        if r["error"]:
            r["error"] = scrub(r["error"])
        for g in r["gateways"]:
            if g["error"]:
                g["error"] = scrub(g["error"])
    ips = [r["exit_ip"] for r in results if r["exit_ip"]]
    dup = len(ips) != len(set(ips))
    ok = all(r["exit_ip"] and all(t["ok"] for t in r["targets"]) and not r["partial"] and not r["inconsistent_ip"]
             for r in results) and not dup
    job.finish(ok, {"accounts": results, "duplicate_ips": dup})


# ----------------------------------------------------------------- acciones sobre VPS

def ssh_base(host):
    opts = ["-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes"]
    if os.path.exists(SSH_KEY):
        opts += ["-i", SSH_KEY]
    opts += shlex.split(os.environ.get("WA_SSH_EXTRA", ""))
    return ["ssh"] + opts + [f'{host["user"]}@{host["ip"]}']


STATUS_SCRIPT = r"""
command -v docker >/dev/null 2>&1 || { echo NODOCKER; exit 0; }
cd ~/wa-proxy 2>/dev/null || { echo NODIR; exit 0; }
TSIP=$(tailscale ip -4 2>/dev/null </dev/null | head -1); echo "TSIP=$TSIP"
docker compose ps -a --format '{{.Service}}|{{.State}}|{{.Status}}' </dev/null 2>/dev/null | sed 's/^/CONT|/'
HOST=$(grep -E '^PROBE_HOST=' .env 2>/dev/null | cut -d= -f2 | tr -d '"'); HOST=${HOST:-api.ipify.org}
for p in $(grep -oE ':53[0-9]{2}:' docker-compose.yml 2>/dev/null | tr -d ':' | sort -u); do
  ( r=$(curl -sk -m 12 --resolve "$HOST:$p:$TSIP" "https://$HOST:$p/?format=json" </dev/null 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)['ip'])" 2>/dev/null); echo "PROBE|$p|$r" ) &
done
wait
"""


def vps_status(host):
    out = {"alias": host["alias"], "ip": host["ip"], "reachable": False, "prepared": False,
           "tailscale_ip": None, "accounts": [], "message": ""}
    try:
        p = subprocess.run(ssh_base(host) + ["bash", "-s"], input=STATUS_SCRIPT, capture_output=True,
                           text=True, timeout=60, cwd=ROOT)
    except subprocess.TimeoutExpired:
        out["message"] = "La VPS tardó demasiado en responder."
        return out
    if p.returncode == 255:
        err = p.stderr.lower()
        if "permission denied" in err:
            out["message"] = "La VPS rechazó la clave SSH: hay que prepararla (paso 2)."
        elif "timed out" in err or "refused" in err or "no route" in err:
            out["message"] = "No se puede conectar a la VPS: revisa la IP y que esté encendida."
        else:
            out["message"] = "No se pudo conectar por SSH."
        return out
    out["reachable"] = True
    lines = p.stdout.splitlines()
    if "NODIR" in lines or "NODOCKER" in lines:
        out["message"] = "La VPS está accesible pero aún no hay nada desplegado."
        out["prepared"] = "NODOCKER" not in lines
        return out
    out["prepared"] = True
    conts, probes = {}, {}
    for ln in lines:
        if ln.startswith("TSIP="):
            out["tailscale_ip"] = ln[5:] or None
        elif ln.startswith("CONT|"):
            _, svc, state, status = (ln.split("|", 3) + ["", "", ""])[:4]
            m = re.match(r"gw-(\d+)$", svc)
            if m:
                conts[int(m.group(1))] = {"state": state, "status": status}
        elif ln.startswith("PROBE|"):
            _, port, ip = (ln.split("|", 2) + [""])[:3]
            if port.isdigit():
                probes[int(port) - 5300] = ip
    for n in sorted(conts):
        out["accounts"].append({"n": n, **conts[n], "exit_ip": probes.get(n) or None})
    if not out["accounts"]:
        out["message"] = "La VPS está preparada pero aún no se ha desplegado."
    return out


def job_prepare(data):
    host = find_host(data["alias"])
    initial_user = str(data.get("initial_user") or "root").strip()
    if not RE_USER.match(initial_user):
        raise ApiError("Usuario inicial inválido")
    password = data.get("password") or ""
    ip = valid_ip_or_host(host["ip"])

    def run(job):
        tmpdir, env = None, {}
        if password:
            tmpdir, env = askpass_env(password)
        try:
            code = run_proc(job, ["bash", "scripts/prepare-vps.sh", f"{initial_user}@{ip}"], env,
                            scrubber({password}))
            job.finish(code == 0)
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)
    return run


def job_deploy(data):
    host = find_host(data["alias"])

    def run(job):
        code = run_proc(job, ["bash", "scripts/deploy.sh", "-t", host["alias"], "--env"])
        job.finish(code == 0)
    return run


def account_power(data):
    host = find_host(data["alias"])
    action = data.get("action")
    if action not in ("start", "stop", "restart"):
        raise ApiError("Acción inválida")
    try:
        n = int(data["n"])
        assert 1 <= n <= 99
    except Exception:
        raise ApiError("Cuenta inválida")
    cmd = f"cd ~/{REMOTE_DIR} && docker compose {action} gw-{n} </dev/null 2>&1"
    p = subprocess.run(ssh_base(host) + [cmd], capture_output=True, text=True, timeout=90, cwd=ROOT)
    return {"ok": p.returncode == 0, "output": scrubber()(p.stdout + p.stderr)[-500:]}


def ensure_key():
    if not os.path.exists(SSH_KEY):
        os.makedirs(os.path.dirname(SSH_KEY), mode=0o700, exist_ok=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "wa-proxy", "-f", SSH_KEY],
                       check=True, capture_output=True)
    with open(SSH_KEY + ".pub") as f:
        return f.read().strip()


def tool_checks():
    return {t: bool(shutil.which(t)) for t in ("ssh", "scp", "bash", "ssh-keygen")}


# ----------------------------------------------------------------- HTTP

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "wa-panel"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if "text" in ctype or "json" in ctype else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _auth(self):
        return hmac.compare_digest(self.headers.get("X-Token", ""), TOKEN)

    def _origin_ok(self):
        o = self.headers.get("Origin")
        return o is None or o in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        u = urllib.parse.urlsplit(self.path)
        if u.path == "/":
            q = urllib.parse.parse_qs(u.query)
            if not hmac.compare_digest(q.get("t", [""])[0], TOKEN):
                return self._send(403, "Abre el enlace completo que mostró el terminal (incluye ?t=...).".encode(), "text/plain")
            with open(INDEX, "rb") as f:
                return self._send(200, f.read(), "text/html")
        if not self._auth():
            return self._send(401, {"error": "token"})
        try:
            if u.path == "/api/state":
                _, probe, _ = read_env()
                return self._send(200, {"accounts": public_accounts(), "vps": read_hosts(),
                                        "probe_host": probe, "tools": tool_checks(),
                                        "ssh_key": os.path.exists(SSH_KEY + ".pub"),
                                        "env_exists": os.path.exists(ENV_FILE)})
            m = re.match(r"^/api/jobs/([0-9a-f]+)$", u.path)
            if m:
                job = JOBS.get(m.group(1))
                if not job:
                    raise ApiError("Trabajo no encontrado", 404)
                since = int(urllib.parse.parse_qs(u.query).get("since", ["0"])[0])
                with job.lock:
                    return self._send(200, {"status": job.status, "lines": job.lines[since:],
                                            "next": len(job.lines), "result": job.result})
            raise ApiError("No encontrado", 404)
        except ApiError as e:
            self._send(e.code, {"error": str(e)})

    def do_POST(self):
        if not (self._host_ok() and self._origin_ok() and self._auth()):
            return self._send(403, {"error": "forbidden"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 100_000:
                raise ApiError("Petición demasiado grande", 413)
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ApiError("Formato inválido")
            p = urllib.parse.urlsplit(self.path).path
            if p == "/api/accounts":
                return self._send(200, {"accounts": save_accounts(data.get("accounts"))})
            if p == "/api/vps":
                return self._send(200, {"vps": add_vps(data)})
            if p == "/api/vps/delete":
                return self._send(200, {"vps": delete_vps(str(data.get("alias", "")))})
            if p == "/api/ssh-key":
                return self._send(200, {"public_key": ensure_key()})
            if p == "/api/verify":
                return self._send(200, {"job": new_job("verify", job_verify)})
            if p == "/api/prepare":
                return self._send(200, {"job": new_job("prepare", job_prepare(data))})
            if p == "/api/deploy":
                return self._send(200, {"job": new_job("deploy", job_deploy(data))})
            if p == "/api/status":
                return self._send(200, vps_status(find_host(str(data.get("alias", "")))))
            if p == "/api/power":
                return self._send(200, account_power(data))
            if p == "/api/quit":
                self._send(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            raise ApiError("No encontrado", 404)
        except ApiError as e:
            self._send(e.code, {"error": str(e)})
        except (KeyError, ValueError, json.JSONDecodeError):
            self._send(400, {"error": "Datos inválidos"})
        except subprocess.TimeoutExpired:
            self._send(504, {"error": "La VPS tardó demasiado en responder"})


def main():
    global PORT
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--open", action="store_true", help="abrir el navegador")
    args = ap.parse_args()
    srv = None
    for port in range(args.port, args.port + 20):
        try:
            PORT = port
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if not srv:
        raise SystemExit("No encontré un puerto libre.")
    url = f"http://127.0.0.1:{PORT}/?t={TOKEN}"
    print(f"\nPanel listo. Abre este enlace en tu navegador:\n\n  {url}\n\n(Ctrl+C para cerrar)", flush=True)
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
