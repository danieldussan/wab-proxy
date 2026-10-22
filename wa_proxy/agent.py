"""Cliente del canal agente ↔ panel (`wa agent ...`).

Códigos de salida:  0 = bien · 1 = el usuario rechazó o la acción falló · 2 = sin respuesta a tiempo
                    3 = el panel no está abierto (ejecuta `wa agent open`)
Los secretos NUNCA pasan por aquí: las credenciales las escribe el usuario en el panel.
"""
import json, os, subprocess, sys, time, urllib.error, urllib.request

from . import core
from .dashboard import SESSION_FILE

POLL = 25


class NoPanel(Exception):
    pass


def load_session():
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def call(path, body=None, timeout=40):
    s = load_session()
    if not s:
        raise NoPanel()
    req = urllib.request.Request(f"http://127.0.0.1:{s['port']}{path}", headers={
        "X-Agent-Token": s["agent_token"], "Content-Type": "application/json", "Host": f"127.0.0.1:{s['port']}"},
        data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error", "")
        except Exception:
            msg = ""
        raise RuntimeError(msg or f"error {e.code}")
    except (urllib.error.URLError, ConnectionError, OSError):
        raise NoPanel()


def alive():
    try:
        return bool(call("/agent/ping", timeout=3).get("ok"))
    except (NoPanel, RuntimeError):
        return False


def open_panel():
    """Abre el panel (lo arranca si hace falta). No imprime el enlace con el token."""
    if alive():
        call("/agent/open", {})
        return True
    kw = {}
    if core.IS_WIN:
        kw["creationflags"] = 0x00000008 | 0x08000000      # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wa.py"), "dashboard", "--open", "--quiet"],
                     cwd=core.ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    for _ in range(40):
        time.sleep(0.25)
        if alive():
            return True
    return False


def wait_request(rid, timeout):
    end = time.time() + timeout
    while time.time() < end:
        r = call(f"/agent/request/{rid}?wait={POLL}", timeout=POLL + 15)
        if r["status"] != "pending":
            return r
    try:
        call(f"/agent/request/{rid}/cancel", {})
    except Exception:
        pass
    return {"status": "timeout", "result": None}


def follow_job(jid, out=print):
    since, last = 0, {}
    while True:
        j = call(f"/agent/jobs/{jid}?since={since}")
        for ln in j["lines"]:
            out(ln)
        since = j["next"]
        if j["status"] != "running":
            return j
        time.sleep(1)


def main(a):
    """a = argparse.Namespace con .sub y sus opciones. -> código de salida."""
    try:
        return _main(a)
    except NoPanel:
        print("El panel no está abierto. Ejecuta primero: wa agent open")
        return 3
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1


def _ask(kind, body, timeout, waiting):
    if not alive():
        raise NoPanel()
    rid = call("/agent/request", dict(body, kind=kind))["request"]
    print(waiting, flush=True)
    r = wait_request(rid, timeout)
    if r["status"] == "done":
        return 0, r["result"]
    if r["status"] == "timeout":
        print("El usuario no respondió a tiempo.")
        return 2, None
    print("El usuario rechazó o canceló la solicitud.")
    return 1, None


def _main(a):
    sub = a.sub
    if sub == "open":
        if open_panel():
            print("Panel abierto en el navegador del usuario.")
            return 0
        print("No pude abrir el panel. Pide al usuario que ejecute: wa dashboard")
        return 1
    if sub == "say":
        call("/agent/say", {"text": " ".join(a.text)})
        return 0
    if sub == "working":
        call("/agent/working", {"text": "" if a.done else " ".join(a.text)})
        return 0
    if sub == "status":
        if a.alias or core.read_hosts():
            st = call("/agent/status", {"alias": a.alias or ""})
            print(json.dumps(st, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(call("/agent/state"), ensure_ascii=False, indent=2))
        return 0
    if sub == "state":
        print(json.dumps(call("/agent/state"), ensure_ascii=False, indent=2))
        return 0
    if sub == "ask-proxy":
        code, res = _ask("proxy", {"n": a.n, "label": a.label, "message": a.message or ""}, a.timeout,
                         "Esperando que el usuario escriba las credenciales del proxy en el panel…")
        if code == 0:
            print(f"Guardado: cuenta {res['n']} (los datos no se muestran por seguridad).")
        return code
    if sub == "ask-vps":
        code, res = _ask("vps", {"message": a.message or ""}, a.timeout, "Esperando que el usuario registre la VPS en el panel…")
        if code == 0:
            print(f"VPS registrada con el nombre «{res['alias']}».")
        return code
    if sub == "confirm":
        code, _ = _ask("confirm", {"message": " ".join(a.text)}, a.timeout, "Esperando la respuesta del usuario en el panel…")
        if code == 0:
            print("El usuario aceptó.")
        return code
    if sub == "run":
        if not alive():
            raise NoPanel()
        body = {"action": a.action, "alias": a.alias or "", "n": a.n, "do": a.do, "message": a.message or ""}
        r = call("/agent/run", body)
        if "request" in r:
            print("Esperando que el usuario apruebe la acción en el panel…", flush=True)
            res = wait_request(r["request"], a.timeout)
            if res["status"] == "timeout":
                print("El usuario no aprobó a tiempo.")
                return 2
            if res["status"] != "done":
                print("El usuario rechazó o canceló la acción.")
                return 1
            jid = res["result"]["job"]
        else:
            jid = r["job"]
        j = follow_job(jid)
        if a.action == "verify" and j["result"]:
            for x in j["result"]["accounts"]:
                print(f"{'[OK]   ' if x['ok'] else '[FALLA]'} cuenta {x['n']}: salida {x['exit_ip'] or '—'}"
                      + (f" ({x['error']})" if x["error"] and not x["ok"] else "")
                      + (" · solo funciona por algunas IPs de la pasarela" if x["partial"] else "")
                      + (" · IP de salida inconsistente entre pasarelas" if x["inconsistent_ip"] else ""))
            if j["result"]["duplicate_ips"]:
                print("[FALLA] Dos cuentas salen por la misma IP")
        return 0 if j["status"] == "ok" else 1
    return 1
