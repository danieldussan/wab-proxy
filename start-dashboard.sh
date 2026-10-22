#!/usr/bin/env bash
# Abre el panel de control en tu navegador (solo escucha en tu equipo).
#   ./start-dashboard.sh            # abre el navegador
#   ./start-dashboard.sh --no-open  # solo imprime el enlace (útil para agentes)
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Necesitas Python 3 (https://www.python.org/downloads/)"; exit 1; }
if [ "${1:-}" = "--no-open" ]; then exec python3 -u dashboard/server.py; fi
exec python3 -u dashboard/server.py --open
