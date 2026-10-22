"""Lógica común (CLI + panel). Solo librería estándar de Python 3.8+.

Funciona igual en Linux, macOS y Windows. Lo único que corre en la VPS es
scripts/bootstrap-vps.sh y los pequeños scripts de este módulo (siempre Linux).
"""
import ipaddress, json, os, re, secrets, shlex, shutil, socket, ssl, stat, struct
import subprocess, sys, tempfile, threading, urllib.parse
from concurrent.futures import ThreadPoolExecutor

IS_WIN = os.name == "nt"
ROOT = os.environ.get("WA_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, ".env")
HOSTS_FILE = os.path.join(ROOT, "hosts.conf")
COMPOSE_FILE = os.path.join(ROOT, "docker-compose.yml")
CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOTSTRAP = os.path.join(CODE_ROOT, "scripts", "bootstrap-vps.sh")
TARGETS = [("g.whatsapp.net", 5222), ("g.whatsapp.net", 443), ("whatsapp.net", 443)]
WA_USER = "wa"
REMOTE_DIR = "wa-proxy"

FILE_LOCK = threading.Lock()

RE_HOST = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
RE_ALIAS = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
RE_USER = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


class ApiError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def ssh_key_path():
    return os.environ.get("WA_SSH_KEY", os.path.expanduser(os.path.join("~", ".ssh", "wa-proxy_ed25519")))


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
            line = raw.rstrip("\r\n")
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


def write_private(path, text):
    """Escribe un archivo con permisos 600 (en Windows chmod casi no aplica)."""
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def write_env(accounts, probe, others):
    lines = ["# Generado por wa-proxy. Puedes editarlo a mano; NO lo compartas.",
             "# Cuenta N usa en la VPS: chat 5100+N, medios 5200+N, sonda 5300+N.", ""]
    for n in sorted(accounts):
        a = accounts[n]
        lines.append(f'PROXY_{n}="socks5://{a["enc_user"]}:{a["enc_pass"]}@{a["host"]}:{a["port"]}"')
        if a.get("label"):
            lines.append(f'LABEL_{n}="{a["label"]}"')
    lines += ["", f'PROBE_HOST="{probe}"'] + others
    write_private(ENV_FILE, "\n".join(lines) + "\n")


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


def upsert_account(it):
    """Añade o actualiza UNA cuenta (it['n'] opcional). Devuelve (n, lista pública)."""
    cur = public_accounts()
    n = int(it["n"]) if str(it.get("n", "")).isdigit() else None
    items = [dict(a, password="") for a in cur]
    if n is not None and any(a["n"] == n for a in items):
        items = [dict(it, n=n) if a["n"] == n else a for a in items]
    else:
        items.append(dict(it, n=n))
    saved = save_accounts(items)
    if n is None:
        n = max(a["n"] for a in saved if a["n"] not in {c["n"] for c in cur})
    return n, saved


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
    body = ["# Generado por wa-proxy. Formato: alias=usuario@ip"]
    body += [f'{h["alias"]}={h["user"]}@{h["ip"]}' for h in hosts]
    tmp = HOSTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
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
    hosts = read_hosts()
    if not alias and len(hosts) == 1:
        return hosts[0]
    for h in hosts:
        if h["alias"] == alias:
            return h
    raise ApiError("VPS no encontrada" if alias else "Indica la VPS (alias)", 404)


# ----------------------------------------------------------------- docker-compose

def generate_compose(accounts=None):
    """Texto del docker-compose.yml: una pasarela gost por cada cuenta."""
    if accounts is None:
        accounts, _, _ = read_env()
    nums = sorted(accounts)
    if not nums:
        raise ApiError("No hay ningún proxy guardado (PROXY_n con valor en .env)")
    out = ["# GENERADO por wa-proxy — no editar a mano.",
           "# Los puertos se atan SOLO a la IP de Tailscale (TS_IP): nada queda expuesto a internet.",
           "", "services:"]
    for n in nums:
        out += [f"  gw-{n}:", "    image: ginuerzh/gost:2.12.0", "    restart: unless-stopped", "    ports:",
                f'      - "${{TS_IP}}:{5100 + n}:5222"', f'      - "${{TS_IP}}:{5200 + n}:7777"',
                f'      - "${{TS_IP}}:{5300 + n}:8443"', "    command: >",
                "      -L tcp://:5222/g.whatsapp.net:5222", "      -L tcp://:7777/whatsapp.net:443",
                "      -L tcp://:8443/${PROBE_HOST:-api.ipify.org}:443", f"      -F ${{PROXY_{n}}}"]
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------- secretos

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
        return sorted({r[4][0] for r in socket.getaddrinfo(host, None, socket.AF_INET)})
    except OSError:
        return []


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


def account_ok(r):
    return bool(r["exit_ip"]) and all(t["ok"] for t in r["targets"]) and not r["partial"] and not r["inconsistent_ip"]


def verify_accounts(log=print):
    """Prueba todas las cuentas. -> (ok, resultado) ; resultado=None si no hay cuentas."""
    accounts, probe, _ = read_env()
    if not accounts:
        log("No hay proxies guardados.")
        return False, None
    log(f"Probando {len(accounts)} proxy(s)…")
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
    ok = all(account_ok(r) for r in results) and not dup
    return ok, {"accounts": results, "duplicate_ips": dup}


def format_verify(res):
    lines = []
    for r in res["accounts"]:
        name = f"Cuenta {r['n']}" + (f" ({r['label']})" if r["label"] else "")
        lines.append(f"{'[OK]   ' if account_ok(r) else '[FALLA]'} {name}: salida {r['exit_ip'] or '—'}"
                     + "".join(f" · {t['target']} {'ok' if t['ok'] else 'NO'}" for t in r["targets"]))
        for g in r["gateways"]:
            lines.append(f"          pasarela {g['gateway']}: {'ok → ' + (g['exit_ip'] or '?') if g['ok'] else 'FALLA (' + str(g['error']) + ')'}")
        if r["partial"]:
            lines.append("          Solo funciona por algunas IPs de la pasarela: el DNS rota y fallará a ratos. Avisa a tu proveedor.")
        elif r["inconsistent_ip"]:
            lines.append("          Cada pasarela da una IP de salida distinta: la IP de la cuenta cambiaría. Avisa a tu proveedor.")
        elif r["error"] and not account_ok(r):
            lines.append(f"          {r['error']}")
    if res["duplicate_ips"]:
        lines.append("[FALLA] Dos cuentas salen por la MISMA IP. Cada cuenta debe tener una IP distinta.")
    return lines


# ----------------------------------------------------------------- procesos / SSH

def run(argv, input=None, env=None, log=None, timeout=None, scrub=None, cwd=None):
    """Ejecuta un proceso y reenvía su salida línea a línea a log(). -> código de salida.

    input: bytes que se escriben por stdin (luego se cierra). Sin input, stdin queda heredado.
    """
    penv = os.environ.copy()
    penv.update(env or {})
    kw = {}
    if IS_WIN:
        kw["creationflags"] = 0x08000000      # CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    try:
        p = subprocess.Popen(argv, cwd=cwd or ROOT, env=penv,
                             stdin=subprocess.PIPE if input is not None else None,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
    except OSError as e:
        (log or print)(f"No se pudo ejecutar «{argv[0]}»: {e}")
        return 127
    if input is not None:
        def feed():
            try:
                p.stdin.write(input)
            except OSError:
                pass
            finally:
                try:
                    p.stdin.close()
                except OSError:
                    pass
        threading.Thread(target=feed, daemon=True).start()
    timer = None
    if timeout:
        timer = threading.Timer(timeout, p.kill)
        timer.start()
    emit = log or print
    scrub = scrub or (lambda s: s)
    try:
        for raw in p.stdout:
            emit(scrub(raw.decode("utf-8", "replace").rstrip("\r\n")))
    finally:
        if timer:
            timer.cancel()
    return p.wait()


def capture(argv, **kw):
    """Como run() pero devuelve (código, texto)."""
    buf = []
    code = run(argv, log=buf.append, **kw)
    return code, "\n".join(buf)


def ssh_opts(batch=True, key=True):
    o = ["-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15"]
    if key and os.path.exists(ssh_key_path()):
        o += ["-i", ssh_key_path()]
    o += shlex.split(os.environ.get("WA_SSH_EXTRA", ""), posix=not IS_WIN)
    if batch:
        o += ["-o", "BatchMode=yes"]
    return o


def ssh_argv(dest, remote, batch=True, key=True):
    return ["ssh"] + ssh_opts(batch, key) + [dest] + ([remote] if remote else [])


def dest_of(h):
    return f'{h["user"]}@{h["ip"]}'


def ensure_key(log=None):
    key = ssh_key_path()
    if not os.path.exists(key):
        d = os.path.dirname(key)
        os.makedirs(d, exist_ok=True)
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass
        code, out = capture(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "wa-proxy", "-f", key])
        if code != 0:
            raise ApiError("No pude crear la clave SSH (¿está instalado el cliente OpenSSH?): " + out[-200:])
        if log:
            log(f"   Clave SSH creada: {key}")
    with open(key + ".pub", encoding="utf-8") as f:
        return f.read().strip()


def askpass_env(password):
    """Entorno para que ssh use la contraseña sin terminal (el script no contiene la clave)."""
    d = tempfile.mkdtemp(prefix="wa-ask-")
    if IS_WIN:
        path = os.path.join(d, "ask.cmd")
        with open(path, "w") as f:
            f.write('@echo off\r\npowershell -NoProfile -Command "Write-Output $env:WA_ROOT_PASS"\r\n')
    else:
        path = os.path.join(d, "ask.sh")
        with open(path, "w") as f:
            f.write('#!/bin/sh\nprintf "%s\\n" "$WA_ROOT_PASS"\n')
        os.chmod(path, 0o700)
    return d, {"SSH_ASKPASS": path, "SSH_ASKPASS_REQUIRE": "force", "DISPLAY": "wa:0", "WA_ROOT_PASS": password}


def tool_checks():
    return {t: bool(shutil.which(t)) for t in ("ssh", "ssh-keygen")}


# ----------------------------------------------------------------- scripts remotos (Linux en la VPS)

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

PROBE_SCRIPT = r"""
cd ~/"$1"
TSIP=$(tailscale ip -4 | head -1)
HOST=$(grep -E '^PROBE_HOST=' .env | cut -d= -f2 | tr -d '"'); HOST=${HOST:-api.ipify.org}
for p in $(grep -oE ':53[0-9]{2}:' docker-compose.yml | tr -d ':' | sort -u); do
  printf '   sonda %s: ' "$p"
  curl -sk -m 15 --resolve "$HOST:$p:$TSIP" "https://$HOST:$p/?format=json" \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['ip'])" 2>/dev/null || echo "FALLO"
done
"""

APPLY_SCRIPT = r"""
set -euo pipefail
pull=$1; cd ~/"$2"
command -v docker >/dev/null || { echo "   Docker no instalado (ejecuta: wa prepare)"; exit 1; }
TSIP=$(tailscale ip -4 | head -1)
[ -n "$TSIP" ] || { echo "   Tailscale sin IP en esta VPS"; exit 1; }
if grep -q '^TS_IP=' .env; then sed -i "s/^TS_IP=.*/TS_IP=$TSIP/" .env; else echo "TS_IP=$TSIP" >> .env; fi
chmod 600 .env
missing=0
for v in $(grep -oE '\$\{PROXY_[0-9]+\}' docker-compose.yml | tr -d '${}' | sort -u); do
  grep -q "^$v=..*" .env || { echo "   FALTA $v en .env"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
docker compose config -q
if [ "$pull" = 1 ]; then docker compose pull; fi
docker compose up -d --remove-orphans
sleep 3
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
echo "   IP de Tailscale (úsala en el iPhone): $TSIP"
"""

BACKUP_CMD = ("mkdir -p ~/{d} && cd ~/{d} && cp -f docker-compose.yml docker-compose.yml.bak 2>/dev/null; "
              "cp -f .env .env.bak 2>/dev/null; true").format(d=REMOTE_DIR)


def vps_status(host):
    out = {"alias": host["alias"], "ip": host["ip"], "reachable": False, "prepared": False,
           "tailscale_ip": None, "accounts": [], "message": "", "msg_key": ""}
    p_out = []
    try:
        code = run(ssh_argv(dest_of(host), "bash -s"), input=STATUS_SCRIPT.encode(), log=p_out.append, timeout=60)
    except Exception as e:                      # pragma: no cover
        out["message"] = str(e)
        return out
    text = "\n".join(p_out)
    if code == 255 or code == 127:
        err = text.lower()
        if code == 127:
            out["message"], out["msg_key"] = "No se encontró el cliente SSH en este equipo.", "no_ssh"
        elif "permission denied" in err:
            out["message"], out["msg_key"] = "La VPS rechazó la clave SSH: hay que prepararla (paso 2).", "denied"
        elif "timed out" in err or "refused" in err or "no route" in err:
            out["message"], out["msg_key"] = "No se puede conectar a la VPS: revisa la IP y que esté encendida.", "unreach"
        else:
            out["message"], out["msg_key"] = "No se pudo conectar por SSH.", "ssh"
        return out
    out["reachable"] = True
    lines = [ln.strip() for ln in text.splitlines()]
    if "NODIR" in lines or "NODOCKER" in lines:
        out["message"], out["msg_key"] = "La VPS está accesible pero aún no hay nada desplegado.", "nothing"
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
        out["message"], out["msg_key"] = "La VPS está preparada pero aún no se ha desplegado.", "notdeployed"
    return out


def power(host, n, action, log=print):
    if action not in ("start", "stop", "restart"):
        raise ApiError("Acción inválida")
    try:
        n = int(n)
        assert 1 <= n <= 99
    except Exception:
        raise ApiError("Cuenta inválida")
    cmd = f"cd ~/{REMOTE_DIR} && docker compose {action} gw-{n} </dev/null 2>&1"
    code = run(ssh_argv(dest_of(host), cmd), log=log, scrub=scrubber(), timeout=90)
    return code == 0


# ----------------------------------------------------------------- prepare / deploy

def _read_bootstrap():
    with open(BOOTSTRAP, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def prepare(dest, password="", log=print):
    """Prepara una VPS nueva (Docker, Tailscale, firewall). dest = usuario@ip."""
    user = dest.split("@")[0]
    scrub = scrubber({password})
    tmpdir, env = (None, {})
    if password:
        tmpdir, env = askpass_env(password)
    try:
        log(f"== 1/3 Acceso por clave SSH a {dest} ==")
        pub = ensure_key(log).encode() + b"\n"
        probe = ssh_argv(dest, "true", batch=True)
        if run(probe, log=lambda s: None, timeout=40, input=b"") == 0:
            log("   Ya hay acceso por clave.")
        else:
            log("   Instalando la clave en la VPS (se usa la contraseña del proveedor, una sola vez)…")
            install = ('umask 077; mkdir -p ~/.ssh; k=$(cat); touch ~/.ssh/authorized_keys; '
                       'grep -qxF "$k" ~/.ssh/authorized_keys || echo "$k" >> ~/.ssh/authorized_keys')
            argv = ["ssh"] + ssh_opts(batch=False, key=False) + ["-o", "NumberOfPasswordPrompts=1", dest, install]
            code = run(argv, input=pub, env=env, log=lambda s: log("   " + s), scrub=scrub, timeout=90)
            if code != 0:
                log("   NO se pudo entrar a la VPS. Revisa: IP, usuario, contraseña, y que la VPS esté encendida.")
                return False
            if run(probe, log=lambda s: None, timeout=40, input=b"") != 0:
                log("   La clave se instaló pero el acceso por clave falla. Revisa permisos de ~/.ssh en la VPS.")
                return False
            log("   Acceso por clave listo.")
        log("== 2/3 Subiendo bootstrap-vps.sh ==")
        if run(ssh_argv(dest, "cat > /tmp/wa-bootstrap.sh"), input=_read_bootstrap(), log=log, timeout=60) != 0:
            log("   No se pudo subir el script.")
            return False
        log("== 3/3 Preparando la VPS (puede tardar unos minutos) ==")
        runner = "bash /tmp/wa-bootstrap.sh" if user == "root" else "sudo -n bash /tmp/wa-bootstrap.sh"
        code = run(ssh_argv(dest, runner), input=b"", log=log, scrub=scrub, timeout=1800)
        run(ssh_argv(dest, "rm -f /tmp/wa-bootstrap.sh"), input=b"", log=lambda s: None, timeout=30)
        if code != 0:
            log("")
            log("LA PREPARACIÓN FALLÓ. Lee el mensaje de error de arriba.")
            if user != "root":
                log("Nota: con un usuario que no es root hace falta sudo sin contraseña; lo normal es usar root.")
            return False
        log("PREPARACIÓN COMPLETA")
        return True
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def _selected(alias):
    hosts = read_hosts()
    if alias:
        hosts = [h for h in hosts if h["alias"] == alias]
    if not hosts:
        raise ApiError("No hay VPS que coincidan en hosts.conf (usa el panel o `wa dashboard` para añadirla)")
    return hosts


def remote_probe(host, log=print):
    return run(ssh_argv(dest_of(host), f"bash -s -- {REMOTE_DIR}"), input=PROBE_SCRIPT.encode(), log=log,
               scrub=scrubber(), timeout=180) == 0


def deploy(alias=None, send_env=True, pull=False, probe=True, log=print):
    """Despliega las pasarelas en una o todas las VPS. -> True si todo salió bien."""
    hosts = _selected(alias)
    if not os.path.exists(ENV_FILE):
        raise ApiError("Falta .env (añade tus proxies primero)")
    compose = generate_compose().encode()
    scrub = scrubber()
    all_ok = True
    for h in hosts:
        d = dest_of(h)
        log(f"=== [{h['alias']}] {d} ===")
        steps_ok = True
        if run(ssh_argv(d, BACKUP_CMD), input=b"", log=log, scrub=scrub, timeout=60) != 0:
            log("   No se pudo conectar a la VPS.")
            all_ok = False
            continue
        if run(ssh_argv(d, f"cat > {REMOTE_DIR}/docker-compose.yml"), input=compose, log=log, timeout=60) != 0:
            log("   Falló la subida de docker-compose.yml")
            all_ok = False
            continue
        log("   docker-compose.yml subido")
        if send_env:
            with open(ENV_FILE, "rb") as f:
                envdata = f.read().replace(b"\r\n", b"\n")
            if run(ssh_argv(d, f"umask 077; cat > {REMOTE_DIR}/.env"), input=envdata, log=log, timeout=60) != 0:
                log("   Falló la subida de .env")
                all_ok = False
                continue
            log("   .env subido (TS_IP se reescribe al aplicar)")
        code = run(ssh_argv(d, f"bash -s -- {1 if pull else 0} {REMOTE_DIR}"), input=APPLY_SCRIPT.encode(),
                   log=log, scrub=scrub, timeout=900)
        if code != 0:
            steps_ok = False
        if steps_ok and probe:
            log("   -- sondas --")
            remote_probe(h, log)
        all_ok = all_ok and steps_ok
        log("")
    return all_ok


def remote_status(alias=None, log=print):
    ok = True
    for h in _selected(alias):
        log(f"=== [{h['alias']}] {dest_of(h)} ===")
        ok &= run(ssh_argv(dest_of(h), f"cd ~/{REMOTE_DIR} && docker compose ps"), input=b"", log=log, timeout=60) == 0
    return ok


def remote_probe_all(alias=None, log=print):
    ok = True
    for h in _selected(alias):
        log(f"=== [{h['alias']}] {dest_of(h)} ===")
        ok &= remote_probe(h, log)
    return ok


def remote_logs(service, alias=None, log=print):
    if not re.match(r"^gw-\d+$", service or ""):
        raise ApiError("Servicio inválido (ej. gw-1)")
    ok = True
    for h in _selected(alias):
        log(f"=== [{h['alias']}] {dest_of(h)} ===")
        ok &= run(ssh_argv(dest_of(h), f"cd ~/{REMOTE_DIR} && docker compose logs --tail 40 {service}"),
                  input=b"", log=log, scrub=scrubber(), timeout=60) == 0
    return ok


# ----------------------------------------------------------------- doctor

def doctor(log=print):
    bad = []

    def ok(m): log(f"[OK]    {m}")

    def fail(m):
        log(f"[FALLA] {m}")
        bad.append(m)

    def warn(m): log(f"[AVISO] {m}")

    if sys.version_info >= (3, 8):
        ok(f"Python {sys.version.split()[0]}")
    else:
        fail("Hace falta Python 3.8 o superior")
    for t in ("ssh", "ssh-keygen"):
        if shutil.which(t):
            ok(f"{t} instalado")
        else:
            fail(f"falta {t}" + (" (Windows: Configuración → Aplicaciones → Características opcionales → Cliente OpenSSH)" if IS_WIN else ""))
    if os.path.exists(ENV_FILE):
        ok(".env existe")
        if IS_WIN:
            warn("En Windows no se puede garantizar el permiso 600 de .env: no compartas esta carpeta")
        elif stat.S_IMODE(os.stat(ENV_FILE).st_mode) == 0o600:
            ok(".env con permisos 600")
        else:
            fail(".env debe ser chmod 600")
        accounts, _, _ = read_env()
        if accounts:
            ok(f"{len(accounts)} proxy(s) definidos")
        else:
            fail("no hay PROXY_n con valor")
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^PROXY_\d+="?(.*?)"?\s*$', line)
                if m and m.group(1) and not re.match(r"socks5h?://", m.group(1)):
                    fail("algún PROXY_n no empieza por socks5://")
                    break
    else:
        fail("falta .env (añade tus proxies desde el panel: `wa dashboard`)")
    hosts = read_hosts()
    if hosts:
        ok(f"{len(hosts)} VPS en hosts.conf")
        if any("203.0.113" in h["ip"] for h in hosts):
            warn("hosts.conf aún tiene la IP de ejemplo")
    else:
        fail("no hay VPS registrada (hosts.conf)")
    if os.path.isdir(os.path.join(ROOT, ".git")) and shutil.which("git"):
        code, _ = capture(["git", "check-ignore", "-q", ".env"])
        if code != 0:
            fail(".env NO está ignorado por git")
    log("")
    if bad:
        log("Hay fallos: corrígelos y vuelve a ejecutar `wa doctor`.")
    else:
        log("Todo listo. Siguiente: `wa verify` y luego `wa deploy`.")
    return not bad
