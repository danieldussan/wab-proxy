#!/usr/bin/env bash
# deploy.sh — despliega las pasarelas gost en una o varias VPS desde tu equipo.
# Lee las VPS de hosts.conf (ver hosts.conf.example) y los proxies de .env.
#
# Uso:
#   ./scripts/deploy.sh --env            # primer despliegue / cambios en .env
#   ./scripts/deploy.sh                  # solo regenera y aplica el compose
#   ./scripts/deploy.sh -t vps1 --env    # una sola VPS (alias de hosts.conf)
#   ./scripts/deploy.sh --pull           # además actualiza la imagen de gost
#   ./scripts/deploy.sh --no-probe       # sin sondas al final
#   ./scripts/deploy.sh status | probe | logs gw-1 [-t vps1]
set -euo pipefail
cd "$(dirname "$0")/.."

HOSTS_FILE=${HOSTS_FILE:-hosts.conf}
REMOTE_DIR="wa-proxy"

[ -f "$HOSTS_FILE" ] || { echo "Falta $HOSTS_FILE (cp hosts.conf.example hosts.conf y edítalo)"; exit 1; }

. scripts/lib.sh
mkdir -p "$HOME/.ssh"
wa_ssh_opts

cmd=deploy
case "${1:-}" in deploy|status|probe|logs) cmd=$1; shift ;; esac

service=""
if [ "$cmd" = logs ]; then
  service=${1:-}; [ -n "$service" ] || { echo "Uso: $0 logs <servicio> [-t alias]"; exit 1; }; shift
fi

target_alias=""; send_env=0; do_pull=0; do_probe=1
while [ $# -gt 0 ]; do
  case "$1" in
    -t|--target) target_alias=${2:?falta alias}; shift 2 ;;
    --env)       send_env=1; shift ;;
    --pull)      do_pull=1; shift ;;
    --no-probe)  do_probe=0; shift ;;
    -h|--help)   sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1"; exit 1 ;;
  esac
done

targets=(); names=()
while IFS= read -r line; do
  line=${line%%#*}; line=$(echo "$line" | xargs)
  [ -n "$line" ] || continue
  name=${line%%=*}; dest=${line#*=}
  if [ -z "$target_alias" ] || [ "$target_alias" = "$name" ]; then names+=("$name"); targets+=("$dest"); fi
done < "$HOSTS_FILE"
[ ${#targets[@]} -gt 0 ] || { echo "No hay VPS que coincidan en $HOSTS_FILE"; exit 1; }

GENERATED=$(mktemp); trap 'rm -f "$GENERATED"' EXIT
if [ "$cmd" = deploy ]; then
  [ -f .env ] || { echo "Falta .env"; exit 1; }
  scripts/generate-compose.sh .env "$GENERATED" >/dev/null
fi

remote_probe() {
  ssh "${SSH_OPTS[@]}" "$1" bash -s -- "$REMOTE_DIR" <<'REMOTE'
cd ~/"$1"
TSIP=$(tailscale ip -4 | head -1)
HOST=$(grep -E '^PROBE_HOST=' .env | cut -d= -f2 | tr -d '"'); HOST=${HOST:-api.ipify.org}
for p in $(grep -oE ':53[0-9]{2}:' docker-compose.yml | tr -d ':' | sort -u); do
  echo -n "   sonda $p: "
  curl -sk -m 15 --resolve "$HOST:$p:$TSIP" "https://$HOST:$p/?format=json" \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['ip'])" 2>/dev/null || echo "FALLO"
done
REMOTE
}

remote_apply() {
  ssh "${SSH_OPTS[@]}" "$1" bash -s -- "$do_pull" "$REMOTE_DIR" <<'REMOTE'
set -euo pipefail
pull=$1; cd ~/"$2"
command -v docker >/dev/null || { echo "   Docker no instalado (ejecuta bootstrap-vps.sh)"; exit 1; }
TSIP=$(tailscale ip -4 | head -1)
[ -n "$TSIP" ] || { echo "   Tailscale sin IP en esta VPS"; exit 1; }
if grep -q '^TS_IP=' .env; then sed -i "s/^TS_IP=.*/TS_IP=$TSIP/" .env; else echo "TS_IP=$TSIP" >> .env; fi
chmod 600 .env
missing=0
for v in $(grep -oE '\$\{PROXY_[0-9]+\}' docker-compose.yml | tr -d '${}' | sort -u); do
  grep -q "^$v=..*" .env || { echo "   FALTA $v en .env (usa --env)"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
docker compose config -q
[ "$pull" = 1 ] && docker compose pull
docker compose up -d --remove-orphans
sleep 3
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
echo "   IP de Tailscale (úsala en el iPhone): $TSIP"
REMOTE
}

for i in "${!targets[@]}"; do
  t=${targets[$i]}; n=${names[$i]}
  echo "=== [$n] $t ==="
  case "$cmd" in
    status) ssh "${SSH_OPTS[@]}" "$t" "cd ~/$REMOTE_DIR && docker compose ps" ;;
    logs)   ssh "${SSH_OPTS[@]}" "$t" "cd ~/$REMOTE_DIR && docker compose logs --tail 40 $service" ;;
    probe)  remote_probe "$t" ;;
    deploy)
      ssh "${SSH_OPTS[@]}" "$t" "mkdir -p ~/$REMOTE_DIR && cd ~/$REMOTE_DIR && cp -f docker-compose.yml docker-compose.yml.bak 2>/dev/null; cp -f .env .env.bak 2>/dev/null; true"
      scp -q "${SSH_OPTS[@]}" "$GENERATED" "$t:$REMOTE_DIR/docker-compose.yml"
      echo "   docker-compose.yml subido"
      if [ "$send_env" = 1 ]; then
        scp -q "${SSH_OPTS[@]}" .env "$t:$REMOTE_DIR/.env"
        echo "   .env subido (TS_IP se reescribe al aplicar)"
      fi
      remote_apply "$t"
      [ "$do_probe" = 1 ] && { echo "   -- sondas --"; remote_probe "$t"; }
      ;;
  esac
  echo
done
