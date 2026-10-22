#!/usr/bin/env bash
# Levanta una "VPS" de prueba LOCAL: Ubuntu 24.04 real (systemd, apt, sshd) en QEMU/KVM,
# con login de root por contraseña, como un proveedor real. No necesita cuentas ni pagos.
# Requiere: qemu-system-x86_64, qemu-img, xorriso, curl y acceso a /dev/kvm.
#
#   tests/vm/start-vm.sh          # crea (si falta) y arranca la VM
#   tests/vm/stop-vm.sh           # la apaga (y con --delete borra el disco)
#
# Variables: VM_DIR (def. ~/.cache/wa-proxy-vm)  VM_SSH_PORT (def. 2230)  VM_ROOT_PASS
#            FAKE_TAILNET=0 para no simular la IP de Tailscale
set -euo pipefail
VM_DIR=${VM_DIR:-$HOME/.cache/wa-proxy-vm}
VM_SSH_PORT=${VM_SSH_PORT:-2230}
VM_ROOT_PASS=${VM_ROOT_PASS:-VpsTest-2026}
IMG_URL=https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

for c in qemu-system-x86_64 qemu-img xorriso curl; do command -v "$c" >/dev/null || { echo "Falta $c"; exit 1; }; done
[ -w /dev/kvm ] || { echo "Sin acceso a /dev/kvm (agrega tu usuario al grupo kvm)"; exit 1; }
mkdir -p "$VM_DIR"; cd "$VM_DIR"
[ -f base.img ] || { echo "Descargando Ubuntu 24.04 (~600 MB)..."; curl -fL -o base.img "$IMG_URL"; }

if [ ! -f vps.qcow2 ]; then
  cat > user-data <<CLOUD
#cloud-config
ssh_pwauth: true
disable_root: false
chpasswd:
  expire: false
  users:
    - {name: root, password: "$VM_ROOT_PASS", type: text}
write_files:
  - path: /etc/ssh/sshd_config.d/01-root.conf
    content: |
      PermitRootLogin yes
      PasswordAuthentication yes
runcmd:
  - systemctl restart ssh
CLOUD
  printf 'instance-id: vps-sim-1\nlocal-hostname: vps-sim\n' > meta-data
  xorriso -as mkisofs -o seed.iso -V cidata -J -r user-data meta-data >/dev/null 2>&1
  qemu-img create -q -f qcow2 -F qcow2 -b base.img vps.qcow2 12G
fi

if [ -f qemu.pid ] && kill -0 "$(cat qemu.pid)" 2>/dev/null; then
  echo "La VM ya está corriendo."
else
  qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -smp 2 -display none -serial file:console.log \
    -daemonize -pidfile qemu.pid -drive file=vps.qcow2,if=virtio -drive file=seed.iso,if=virtio,format=raw \
    -nic "user,hostfwd=tcp:127.0.0.1:$VM_SSH_PORT-:22"
fi

# askpass: ssh usa la contraseña sin terminal (igual que hace el panel)
printf '#!/bin/sh\nprintf "%%s\\n" "%s"\n' "$VM_ROOT_PASS" > askpass.sh; chmod 700 askpass.sh
vmssh() {
  SSH_ASKPASS="$VM_DIR/askpass.sh" SSH_ASKPASS_REQUIRE=force DISPLAY=x setsid \
    ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$VM_DIR/known_hosts" -o PubkeyAuthentication=no \
        -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 -p "$VM_SSH_PORT" root@127.0.0.1 "$@" </dev/null
}
echo -n "Esperando a que la VM arranque"
for _ in $(seq 1 60); do
  vmssh 'cloud-init status --wait >/dev/null 2>&1; true' 2>/dev/null && break
  echo -n .; sleep 4
done
echo

# Tailscale no se puede autorizar sin cuenta: simulamos su IP, que aparece 25 s DESPUÉS de arrancar
# (así se prueba la regla "Docker espera a Tailscale").
if [ "${FAKE_TAILNET:-1}" = 1 ]; then
  vmssh "$(cat <<'REMOTE'
[ -x /usr/bin/tailscale ] || curl -fsSL https://tailscale.com/install.sh | sh >/dev/null 2>&1
cat > /usr/local/bin/tailscale <<'SHIM'
#!/bin/sh
if [ "$1" = ip ]; then ip -4 addr show dev lo | grep -q "100.64.0.1" && { echo 100.64.0.1; exit 0; } || exit 1; fi
exec /usr/bin/tailscale "$@"
SHIM
chmod +x /usr/local/bin/tailscale
cat > /etc/systemd/system/fake-tailnet.service <<'UNIT'
[Unit]
Description=Simula tailscale0 apareciendo tarde
[Service]
ExecStart=/bin/sh -c "sleep 25; ip addr add 100.64.0.1/32 dev lo; sleep infinity"
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload; systemctl enable fake-tailnet.service >/dev/null 2>&1
ip addr show dev lo | grep -q 100.64.0.1 || ip addr add 100.64.0.1/32 dev lo
REMOTE
)"
fi

cat <<TXT

VM lista.  IP: 127.0.0.1   puerto SSH: $VM_SSH_PORT   usuario: root   contraseña: $VM_ROOT_PASS

Para usarla con el panel o con ./wa prepare / ./wa deploy (los proxies de prueba deben apuntar a 10.0.2.2, que es tu equipo visto desde la VM):
  python3 tests/fake_socks5.py 19201 usuario clave &        # proxy SOCKS5 falso
  export WA_SSH_KEY=$VM_DIR/wakey
  export WA_SSH_EXTRA="-o Port=$VM_SSH_PORT -o UserKnownHostsFile=$VM_DIR/known_hosts"
  ./wa dashboard
En el panel: proxy servidor 10.0.2.2, puerto 19201 · VPS IP 127.0.0.1 · Preparar (usuario root + contraseña de arriba).
TXT
