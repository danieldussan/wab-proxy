#!/usr/bin/env bash
# Prepara una VPS NUEVA (Debian/Ubuntu). Normalmente lo lanza prepare-vps.sh;
# también puede ejecutarse a mano como root EN la VPS.
# Hace: usuario "wa" con tu clave SSH, Docker, Tailscale, firewall (solo SSH),
# fail2ban y orden de arranque (Docker espera a Tailscale tras un reinicio).
# Variables opcionales: WA_USER=wa
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Ejecuta como root (o con sudo)"; exit 1; }
command -v apt-get >/dev/null || { echo "Solo se soporta Debian/Ubuntu (apt-get)."; exit 1; }
WA_USER=${WA_USER:-wa}
export DEBIAN_FRONTEND=noninteractive
APT=(apt-get -o DPkg::Lock::Timeout=300 -y)

echo "== 1/6 Paquetes base =="
"${APT[@]}" update
"${APT[@]}" install curl ca-certificates ufw python3 jq fail2ban

echo "== 2/6 Docker =="
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

echo "== 3/6 Usuario $WA_USER =="
id "$WA_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$WA_USER"
groupadd -f docker
usermod -aG docker "$WA_USER"
KEYS_SRC=""
for f in /root/.ssh/authorized_keys "/home/${SUDO_USER:-nobody}/.ssh/authorized_keys"; do
  [ -s "$f" ] && { KEYS_SRC=$f; break; }
done
if [ -n "$KEYS_SRC" ]; then
  install -d -m 700 -o "$WA_USER" -g "$WA_USER" "/home/$WA_USER/.ssh"
  cp "$KEYS_SRC" "/home/$WA_USER/.ssh/authorized_keys"
  chown "$WA_USER:$WA_USER" "/home/$WA_USER/.ssh/authorized_keys"
  chmod 600 "/home/$WA_USER/.ssh/authorized_keys"
  echo "   Claves SSH copiadas a $WA_USER"
else
  echo "AVISO: no encontré authorized_keys para copiar; configura la clave SSH de $WA_USER a mano."
fi

echo "== 4/6 Tailscale =="
command -v tailscale >/dev/null || curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled
if ! tailscale ip -4 >/dev/null 2>&1; then
  echo ">> AUTORIZA ESTA VPS: abre el enlace de Tailscale que aparece abajo (tienes 10 minutos)"
  timeout 600 tailscale up </dev/null || { echo "Tailscale no fue autorizado a tiempo. Vuelve a ejecutar la preparación."; exit 1; }
fi
echo "   IP de Tailscale: $(tailscale ip -4 | head -1)"

echo "== 5/6 Docker espera a Tailscale al reiniciar =="
# Los puertos se publican en la IP de Tailscale: si Docker arranca antes de que
# exista, los contenedores no levantan tras un reinicio de la VPS.
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/wait-tailscale.conf <<'EOT'
[Unit]
After=tailscaled.service
Wants=tailscaled.service

[Service]
ExecStartPre=-/bin/sh -c 'timeout 90 sh -c "until tailscale ip -4 >/dev/null 2>&1; do sleep 1; done"'
EOT
systemctl daemon-reload

echo "== 6/6 Firewall (solo SSH entrante público) y fail2ban =="
# awk lee todo (sin exit) para que sshd no reciba SIGPIPE y pipefail no aborte
SSH_PORT=$( { sshd -T 2>/dev/null || true; } | awk '/^port /{p=$2} END{print p}')
ufw default deny incoming
ufw default allow outgoing
ufw allow "${SSH_PORT:-22}/tcp"
ufw allow in on tailscale0
ufw --force enable
systemctl enable --now fail2ban

echo
echo "Listo. IP de Tailscale de esta VPS: $(tailscale ip -4 | head -1)"
