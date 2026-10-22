#!/usr/bin/env bash
# doctor.sh — diagnóstico rápido LOCAL: ¿está todo listo para desplegar?
# Salida: [OK] / [FALLA] / [AVISO] por revisión. No imprime secretos.
cd "$(dirname "$0")/.."
bad=0
ok()   { echo "[OK]    $*"; }
fail() { echo "[FALLA] $*"; bad=1; }
warn() { echo "[AVISO] $*"; }

for c in ssh scp python3; do command -v $c >/dev/null && ok "$c instalado" || fail "falta $c"; done
for c in curl jq; do command -v $c >/dev/null || warn "falta $c (solo lo necesita scripts/verify-proxies.sh; el dashboard no)"; done

if [ -f .env ]; then
  ok ".env existe"
  perm=$(stat -c %a .env 2>/dev/null || stat -f %Lp .env 2>/dev/null)
  [ "$perm" = 600 ] && ok ".env con permisos 600" || fail ".env debe ser chmod 600"
  n=$(grep -cE '^PROXY_[0-9]+="?[^"]' .env || true)
  [ "$n" -ge 1 ] && ok "$n proxy(s) definidos" || fail "no hay PROXY_n con valor"
  grep -E '^PROXY_[0-9]+="?[^"]' .env | grep -vqE '"?socks5h?://' && fail "algún PROXY_n no empieza por socks5://"
  grep -qE '^PROXY_[0-9]+="?socks5h?://[^"]*@[^"]*@' .env && warn "hay más de una @ en alguna URL: codifica la clave (@ -> %40)"
else
  fail "falta .env (cp .env.example .env && chmod 600 .env)"
fi

if [ -f hosts.conf ]; then
  v=$(grep -vE '^\s*(#|$)' hosts.conf | wc -l)
  [ "$v" -ge 1 ] && ok "$v VPS en hosts.conf" || fail "hosts.conf vacío"
  grep -q '203.0.113' hosts.conf && warn "hosts.conf aún tiene la IP de ejemplo"
else
  fail "falta hosts.conf (cp hosts.conf.example hosts.conf)"
fi

git check-ignore -q .env 2>/dev/null || { [ -d .git ] && fail ".env NO está ignorado por git"; }

echo
[ $bad = 0 ] && echo "Todo listo. Siguiente: ./scripts/verify-proxies.sh y luego ./scripts/deploy.sh --env" || echo "Hay fallos: corrígelos y vuelve a ejecutar."
exit $bad
