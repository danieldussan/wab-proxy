#!/usr/bin/env bash
# Verifica los proxies del .env SIN teléfono y SIN VPS:
#   1) IP de salida de cada proxy (distinta entre cuentas)
#   2) Alcance TCP a los destinos de WhatsApp
# Se prueba CADA IP que hay detrás del nombre del proxy: muchos proveedores reparten
# el DNS entre varias pasarelas, y si una falla el proxy parece "intermitente".
# No imprime credenciales. Requiere: curl, jq, python3.
set -uo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] || { echo "Falta .env — cp .env.example .env && chmod 600 .env"; exit 1; }
for c in curl jq python3; do command -v $c >/dev/null || { echo "Instala $c"; exit 1; }; done
set -a; . ./.env; set +a

PROBE_HOST=${PROBE_HOST:-api.ipify.org}
targets=(g.whatsapp.net:5222 g.whatsapp.net:443 whatsapp.net:443)

# curl con el proxy pasado por stdin (así la clave no aparece en `ps`)
pcurl() { local u=$1; shift; printf 'proxy = "%s"\n' "$u" | curl -K - "$@"; }
mask() { sed -E 's|//[^@]*@|//***@|'; }
gateway_ips() {
  python3 -c 'import socket,sys
try: print("\n".join(sorted({r[4][0] for r in socket.getaddrinfo(sys.argv[1], None, socket.AF_INET)})))
except OSError: pass' "$1"
}

ips=(); fail=0; found=0

for var in $(compgen -A variable | grep -E '^PROXY_[0-9]+$' | sort -t_ -k2 -n); do
  base="${!var}"
  [ -n "$base" ] || continue
  found=1
  base="$(printf '%s' "$base" | sed 's|^socks5://|socks5h://|')"   # DNS EN el proxy (imprescindible)
  rest=${base##*@}; host=${rest%%:*}; port=${rest##*:}; prefix=${base%@*}
  gws=$(gateway_ips "$host"); [ -n "$gws" ] || gws=$host
  n_gw=$(printf '%s\n' "$gws" | wc -l)
  echo "== $var  [$(printf '%s' "$base" | mask)]  ($n_gw pasarela(s))"

  ok_gw=0; acc_ips=()
  for gw in $gws; do
    url="$prefix@$gw:$port"
    ip="$(pcurl "$url" -s --max-time 15 "https://$PROBE_HOST/?format=json" 2>/dev/null | jq -r '.ip // empty' 2>/dev/null)"
    if [ -z "$ip" ]; then
      echo "   pasarela $gw: FALLA (sin respuesta; revisa usuario/clave/puerto o avisa a tu proveedor)"
      continue
    fi
    # Los 3 destinos en paralelo. curl telnet:// no termina solo, así que se corta a los 5 s
    # (la línea "Opened SOCKS connection" aparece mucho antes si el proxy sí conecta).
    tmp=$(mktemp -d); i=0
    for t in "${targets[@]}"; do
      i=$((i + 1))
      ( pcurl "$url" -sv --max-time 5 "telnet://$t" 2>&1 | grep -cE 'Opened SOCKS connection|SOCKS5 request granted' > "$tmp/$i" ) &
    done
    wait; bad=0; i=0
    for t in "${targets[@]}"; do
      i=$((i + 1))
      [ "$(cat "$tmp/$i")" -ge 1 ] || { echo "   pasarela $gw: $t -> FALLA"; bad=1; }
    done
    rm -rf "$tmp"
    if [ "$bad" = 0 ]; then
      echo "   pasarela $gw: OK  IP de salida: $ip"
      ok_gw=$((ok_gw + 1)); acc_ips+=("$ip")
    fi
  done

  if [ "$ok_gw" -eq 0 ]; then
    fail=1
  elif [ "$ok_gw" -lt "$n_gw" ]; then
    echo "   ALERTA: funciona solo por $ok_gw de $n_gw pasarelas. El DNS rota entre ellas, así que fallará"
    echo "           de forma intermitente. Pide a tu proveedor que lo corrija."
    fail=1
  fi
  if [ "$ok_gw" -gt 0 ] && [ "$(printf '%s\n' "${acc_ips[@]}" | sort -u | wc -l)" -gt 1 ]; then
    echo "   ALERTA: cada pasarela devuelve una IP de salida distinta (la IP de la cuenta cambiaría)."
    fail=1
  fi
  [ "$ok_gw" -gt 0 ] && ips+=("$var=${acc_ips[0]}")
  echo
done

[ "$found" = 1 ] || { echo "No hay PROXY_n con valor en .env"; exit 1; }

if [ "${#ips[@]}" -ge 2 ]; then
  uniq_ips="$(printf '%s\n' "${ips[@]#*=}" | sort -u | wc -l)"
  if [ "$uniq_ips" -eq "${#ips[@]}" ]; then echo "IPs distintas entre cuentas: OK"
  else echo "ALERTA: hay IPs repetidas entre cuentas"; fail=1; fi
fi

if [ "$fail" -eq 0 ]; then echo "RESULTADO: PASS"; else echo "RESULTADO: FALLO (ver arriba)"; fi
exit "$fail"
