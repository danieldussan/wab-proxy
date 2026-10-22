"""Línea de comandos de wa-proxy:  wa <comando> ...   (Linux, macOS y Windows)"""
import argparse, os, sys

from . import core
from .core import ApiError

HELP_EPILOG = """\
Comandos principales:
  wa dashboard           abre el panel web (recomendado)
  wa doctor              revisa que todo esté listo
  wa verify              prueba tus proxies
  wa prepare IP          prepara una VPS nueva
  wa deploy              despliega los proxies en la VPS
  wa status | probe | logs gw-1
Para agentes de IA:  wa agent --help
"""


def build_parser():
    p = argparse.ArgumentParser(prog="wa", description="Proxies SOCKS5 por cuenta de WhatsApp (VPS + Tailscale).",
                                epilog=HELP_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd")
    sp.add_parser("doctor", help="diagnóstico local")
    sp.add_parser("verify", help="probar los proxies del .env")
    c = sp.add_parser("compose", help="generar docker-compose.yml")
    c.add_argument("-o", "--out", default=core.COMPOSE_FILE)
    c = sp.add_parser("prepare", help="preparar una VPS nueva")
    c.add_argument("dest", help="[usuario@]IP o alias de hosts.conf")
    c = sp.add_parser("deploy", help="desplegar en la(s) VPS")
    c.add_argument("-t", "--target", help="alias de la VPS (por defecto todas)")
    c.add_argument("--no-env", action="store_true", help="no subir .env")
    c.add_argument("--pull", action="store_true", help="actualizar la imagen de gost")
    c.add_argument("--no-probe", action="store_true")
    for name in ("status", "probe"):
        c = sp.add_parser(name)
        c.add_argument("-t", "--target")
    c = sp.add_parser("logs")
    c.add_argument("service", help="ej. gw-1")
    c.add_argument("-t", "--target")
    c = sp.add_parser("dashboard", help="abrir el panel web")
    c.add_argument("--port", type=int, default=8787)
    c.add_argument("--no-open", action="store_true", help="no abrir el navegador (solo imprime el enlace)")
    c.add_argument("--open", action="store_true", help=argparse.SUPPRESS)
    c.add_argument("--quiet", action="store_true", help=argparse.SUPPRESS)

    ag = sp.add_parser("agent", help="canal para agentes de IA ↔ panel")
    asub = ag.add_subparsers(dest="sub", required=True)
    asub.add_parser("open", help="abrir el panel al usuario")
    x = asub.add_parser("say", help="mostrar un mensaje en el panel")
    x.add_argument("text", nargs="+")
    x = asub.add_parser("working", help="indicar qué estás haciendo")
    x.add_argument("text", nargs="*")
    x.add_argument("--done", action="store_true")
    x = asub.add_parser("ask-proxy", help="pedir credenciales de un proxy al usuario")
    x.add_argument("--n", type=int)
    x.add_argument("--label", default="")
    x.add_argument("--message")
    x = asub.add_parser("ask-vps", help="pedir la VPS al usuario")
    x.add_argument("--message")
    x = asub.add_parser("confirm", help="pedir confirmación (sí/no)")
    x.add_argument("text", nargs="+")
    x = asub.add_parser("run", help="ejecutar una acción (verify, prepare, deploy, power)")
    x.add_argument("action", choices=["verify", "prepare", "deploy", "power"])
    x.add_argument("--alias")
    x.add_argument("--n", type=int)
    x.add_argument("--do", choices=["start", "stop", "restart"])
    x.add_argument("--message")
    x = asub.add_parser("status", help="estado de la VPS")
    x.add_argument("--alias")
    asub.add_parser("state", help="resumen (sin secretos)")
    for name in ("ask-proxy", "ask-vps", "confirm", "run"):
        asub.choices[name].add_argument("--timeout", type=int, default=900, help="segundos de espera")
    return p


def cmd_prepare(dest):
    hosts = core.read_hosts()
    for h in hosts:
        if h["alias"] == dest:
            dest = f"root@{h['ip']}"
    if "@" not in dest:
        dest = f"root@{dest}"
    return core.prepare(dest)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = build_parser()
    a = p.parse_args(argv)
    try:
        if a.cmd == "doctor":
            return 0 if core.doctor() else 1
        if a.cmd == "verify":
            ok, res = core.verify_accounts()
            if res is None:
                return 1
            print("\n".join(core.format_verify(res)))
            print("\n" + ("Todos los proxies funcionan." if ok else "Hay problemas: revisa lo de arriba."))
            return 0 if ok else 1
        if a.cmd == "compose":
            with open(a.out, "w", encoding="utf-8", newline="\n") as f:
                f.write(core.generate_compose())
            print(f"Generado {a.out}")
            return 0
        if a.cmd == "prepare":
            return 0 if cmd_prepare(a.dest) else 1
        if a.cmd == "deploy":
            return 0 if core.deploy(a.target, not a.no_env, a.pull, not a.no_probe) else 1
        if a.cmd == "status":
            return 0 if core.remote_status(a.target) else 1
        if a.cmd == "probe":
            return 0 if core.remote_probe_all(a.target) else 1
        if a.cmd == "logs":
            return 0 if core.remote_logs(a.service, a.target) else 1
        if a.cmd == "dashboard":
            from . import agent, dashboard
            if agent.alive():
                agent.call("/agent/open", {})
                print("El panel ya estaba abierto: lo he traído al navegador.")
                return 0
            dashboard.serve(a.port, not a.no_open, a.quiet)
            return 0
        if a.cmd == "agent":
            from . import agent
            return agent.main(a)
    except ApiError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        return 130
    p.print_help()
    return 0
