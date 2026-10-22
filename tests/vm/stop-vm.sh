#!/usr/bin/env bash
# Apaga la VM de prueba.  --delete borra también el disco (conserva la imagen base descargada).
VM_DIR=${VM_DIR:-$HOME/.cache/wa-proxy-vm}
if [ -f "$VM_DIR/qemu.pid" ] && kill "$(cat "$VM_DIR/qemu.pid")" 2>/dev/null; then echo "VM apagada."; fi
rm -f "$VM_DIR/qemu.pid"
if [ "${1:-}" = "--delete" ]; then
  rm -f "$VM_DIR"/{vps.qcow2,seed.iso,user-data,meta-data,known_hosts,console.log,askpass.sh}
  echo "Disco borrado."
fi
