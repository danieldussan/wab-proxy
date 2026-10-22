#!/usr/bin/env bash
# Prepara una VPS NUEVA desde tu equipo, en un solo comando:
#   ./scripts/prepare-vps.sh [usuario@]IP        (usuario por defecto: root)
# Hace: crea/usa tu clave SSH del proyecto, la instala en la VPS (te pide la
# contraseña del proveedor UNA vez si hace falta) y ejecuta bootstrap-vps.sh
# (usuario "wa", Docker, Tailscale, firewall). Al final te pedirá autorizar
# Tailscale abriendo una URL.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/lib.sh

dest=${1:?Uso: $0 [usuario@]IP}
[[ $dest == *@* ]] || dest="root@$dest"
user=${dest%@*}

wa_ensure_key
wa_ssh_opts
BASE=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
# shellcheck disable=SC2206
[ -n "${WA_SSH_EXTRA:-}" ] && BASE+=($WA_SSH_EXTRA)

echo "== 1/3 Acceso por clave SSH a $dest =="
if ssh "${BASE[@]}" -i "$WA_SSH_KEY" -o BatchMode=yes "$dest" true 2>/dev/null; then
  echo "   Ya hay acceso por clave."
else
  echo "   Instalando la clave en la VPS (se usará la contraseña del proveedor, una sola vez)..."
  if ! ssh "${BASE[@]}" "$dest" \
      'umask 077; mkdir -p ~/.ssh; k=$(cat); touch ~/.ssh/authorized_keys; grep -qxF "$k" ~/.ssh/authorized_keys || echo "$k" >> ~/.ssh/authorized_keys' \
      < "$WA_SSH_KEY.pub"; then
    echo "   NO se pudo entrar a la VPS. Revisa: IP, usuario, contraseña, y que la VPS esté encendida."
    exit 1
  fi
  ssh "${BASE[@]}" -i "$WA_SSH_KEY" -o BatchMode=yes "$dest" true \
    || { echo "   La clave se instaló pero el acceso por clave falla. Revisa permisos de ~/.ssh en la VPS."; exit 1; }
  echo "   Acceso por clave listo."
fi

echo "== 2/3 Subiendo bootstrap-vps.sh =="
ssh "${SSH_OPTS[@]}" "$dest" 'cat > /tmp/wa-bootstrap.sh' < scripts/bootstrap-vps.sh

echo "== 3/3 Preparando la VPS (puede tardar unos minutos) =="
if [ "$user" = root ]; then run='bash /tmp/wa-bootstrap.sh'; else run='sudo -n bash /tmp/wa-bootstrap.sh'; fi
if ! ssh "${SSH_OPTS[@]}" "$dest" "$run" </dev/null; then
  ssh "${SSH_OPTS[@]}" "$dest" 'rm -f /tmp/wa-bootstrap.sh' </dev/null || true
  echo
  echo "LA PREPARACIÓN FALLÓ. Lee el mensaje de error de arriba."
  [ "$user" = root ] || echo "Nota: con un usuario que no es root hace falta sudo sin contraseña; lo normal es usar root."
  exit 1
fi
ssh "${SSH_OPTS[@]}" "$dest" 'rm -f /tmp/wa-bootstrap.sh' </dev/null || true
echo "PREPARACIÓN COMPLETA"
