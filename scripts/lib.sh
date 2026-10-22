#!/usr/bin/env bash
# Funciones comunes. Se usa con:  . "$(dirname "$0")/lib.sh"
# Variables:
#   WA_SSH_KEY   clave SSH propia del proyecto (def. ~/.ssh/wa-proxy_ed25519)
#   WA_SSH_EXTRA opciones extra de ssh/scp (ej. "-o Port=2222")
#   WA_BATCH=1   modo no interactivo (lo usa el dashboard): sin preguntas ni multiplexado

WA_SSH_KEY=${WA_SSH_KEY:-$HOME/.ssh/wa-proxy_ed25519}

wa_ensure_key() {
  mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
  if [ ! -f "$WA_SSH_KEY" ]; then
    ssh-keygen -q -t ed25519 -N "" -C "wa-proxy" -f "$WA_SSH_KEY"
    echo "   Clave SSH creada: $WA_SSH_KEY"
  fi
}

# Opciones de ssh/scp para conectar con la clave del proyecto (si existe).
wa_ssh_opts() {
  SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o ServerAliveInterval=15)
  [ -f "$WA_SSH_KEY" ] && SSH_OPTS+=(-i "$WA_SSH_KEY")
  # Opciones extra, p. ej. puerto SSH distinto:  WA_SSH_EXTRA="-o Port=2222"
  # shellcheck disable=SC2206
  [ -n "${WA_SSH_EXTRA:-}" ] && SSH_OPTS+=($WA_SSH_EXTRA)
  if [ "${WA_BATCH:-0}" = 1 ]; then
    SSH_OPTS+=(-o BatchMode=yes)
  else
    SSH_OPTS+=(-o ControlMaster=auto -o "ControlPath=$HOME/.ssh/cm-%C" -o ControlPersist=10m)
  fi
}
