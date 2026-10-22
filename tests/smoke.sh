#!/usr/bin/env bash
# Pruebas rápidas sin VPS ni proxies reales. Trabaja en una COPIA temporal:
# nunca toca tu .env ni tu hosts.conf.   Uso: tests/smoke.sh
set -euo pipefail
SRC=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"; kill $(jobs -p) 2>/dev/null || true' EXIT
tar -C "$SRC" --exclude=.env --exclude=hosts.conf --exclude=docker-compose.yml --exclude=.git -cf - . | tar -C "$TMP" -xf -
cd "$TMP"
pass() { echo "[OK]    $*"; }

for f in scripts/*.sh start-dashboard.sh; do bash -n "$f"; done; pass "sintaxis de scripts"
python3 -m py_compile dashboard/server.py tests/fake_socks5.py; pass "python compila"

printf 'PROXY_1="socks5://u:p@h:1"\nPROXY_3="socks5://u:p@h:3"\nPROXY_4=""\n' > .env
scripts/generate-compose.sh >/dev/null
grep -q 'gw-1:' docker-compose.yml && grep -q 'gw-3:' docker-compose.yml && ! grep -q 'gw-4:' docker-compose.yml \
  && grep -q '5103:5222' docker-compose.yml && grep -q 'gost:2.12.0' docker-compose.yml
pass "generate-compose (huecos y puertos)"
rm -f .env docker-compose.yml

WA_TEST_ROOT="$TMP" python3 -W ignore tests/test_dashboard.py
pass "dashboard"
