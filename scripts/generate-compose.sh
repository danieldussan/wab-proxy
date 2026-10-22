#!/usr/bin/env bash
# Genera docker-compose.yml con una pasarela gost por cada PROXY_n del .env.
# Puertos por cuenta n:  chat 5100+n | medios 5200+n | sonda 5300+n   (n = 1..99)
# Uso: scripts/generate-compose.sh [ruta-del-.env] [ruta-de-salida]
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=${1:-.env}
OUT=${2:-docker-compose.yml}
[ -f "$ENV_FILE" ] || { echo "No existe $ENV_FILE (copia .env.example a .env)"; exit 1; }

# Solo lee NOMBRES de variables con valor; nunca imprime los valores.
nums=$(grep -E '^PROXY_[0-9]+="?[^"]' "$ENV_FILE" | sed -E 's/^PROXY_([0-9]+)=.*/\1/' | sort -n | uniq)
[ -n "$nums" ] || { echo "No hay ningún PROXY_n con valor en $ENV_FILE"; exit 1; }

{
  echo "# GENERADO por scripts/generate-compose.sh — no editar a mano."
  echo "# Los puertos se atan SOLO a la IP de Tailscale (TS_IP): nada queda expuesto a internet."
  echo
  echo "services:"
  for n in $nums; do
    echo "  gw-$n:"
    echo "    image: ginuerzh/gost:2.12.0"
    echo "    restart: unless-stopped"
    echo "    ports:"
    echo "      - \"\${TS_IP}:$((5100 + n)):5222\""
    echo "      - \"\${TS_IP}:$((5200 + n)):7777\""
    echo "      - \"\${TS_IP}:$((5300 + n)):8443\""
    echo "    command: >"
    echo "      -L tcp://:5222/g.whatsapp.net:5222"
    echo "      -L tcp://:7777/whatsapp.net:443"
    echo "      -L tcp://:8443/\${PROBE_HOST:-api.ipify.org}:443"
    echo "      -F \${PROXY_$n}"
  done
} > "$OUT"

echo "Generado $OUT con $(echo "$nums" | wc -w) cuenta(s): $(echo $nums)"
