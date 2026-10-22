# AGENTS.md — guía para agentes de IA (Claude Code, Codex, OpenCode…)

Objetivo: ayudar a una persona (probablemente **no técnica**) a dejar funcionando proxies de WhatsApp **por cuenta** en una VPS. Responde en el idioma del usuario, explica cada paso en una frase y verifica antes de avanzar.

## Forma preferida: abrir el panel

El repo trae un panel web local. **Úsalo en vez de pedir datos por el chat.**

1. Comprueba lo básico: `./scripts/doctor.sh` (necesita `python3` y `ssh`).
2. Arranca el panel en segundo plano: `./start-dashboard.sh --no-open` y lee de su salida el enlace `http://127.0.0.1:PUERTO/?t=TOKEN`.
3. Dale ese enlace al usuario y dile que lo abra en su navegador. Si el agente corre en otra máquina (nube, SSH), el usuario necesita un túnel: `ssh -L PUERTO:127.0.0.1:PUERTO usuario@maquina`.
4. Explícale los 4 pasos del panel (proxies → VPS → estado → iPhone) y acompáñalo. El panel muestra «Siguiente paso» en un banner.
5. **Las contraseñas (proxies y root de la VPS) las escribe el usuario en el panel. Nunca en el chat.**

También puedes ayudar desde la terminal con los scripts (tabla abajo) para diagnosticar.

## Reglas de seguridad (obligatorias)

1. **Nunca leas, imprimas ni pegues el contenido de `.env` ni de `hosts.conf`.** Para revisarlos usa `./scripts/doctor.sh`. Para confirmar una variable: `grep -c '^PROXY_1=' .env`, nunca `cat`.
2. **Nunca hagas commit de `.env`, `hosts.conf` ni `docker-compose.yml`** (están en `.gitignore`; no uses `git add -f`).
3. Si el usuario pega credenciales en el chat, avísale de que debe rotarlas y que las escriba solo en el panel.
4. Antes de ejecutar nada que modifique una VPS (`prepare-vps.sh`, `deploy.sh`, `docker compose stop/down`), di qué vas a hacer y pide confirmación.
5. No abras puertos al público. Todo escucha solo en la IP de Tailscale. No cambies el firewall salvo petición explícita.
6. No prometas que WhatsApp no bloqueará las cuentas. Recuerda: números de prueba, y las llamadas NO pasan por el proxy.
7. No cambies el panel para que escuche fuera de `127.0.0.1` ni para que devuelva contraseñas.

## Flujo manual (equivalente al panel)

| # | Paso | Comando | Éxito si |
|---|---|---|---|
| 0 | Entorno local | `./scripts/doctor.sh` | todo `[OK]` |
| 1 | Proxies | `./scripts/verify-proxies.sh` | `RESULTADO: PASS`, IPs distintas |
| 2 | VPS nueva | `./scripts/prepare-vps.sh root@IP` (pide la contraseña del proveedor una vez y una URL de Tailscale que el usuario debe autorizar) | termina en `PREPARACIÓN COMPLETA` |
| 3 | Desplegar | añadir `wa@IP` a `hosts.conf` → `./scripts/deploy.sh --env` | contenedores `Up` y sondas con las IPs esperadas |
| 4 | iPhone | `docs/03-configurar-iphone.md` | mensajes, fotos y audio funcionan |

Diagnóstico: `./scripts/deploy.sh status | probe | logs gw-N` y `docs/04-troubleshooting.md`.

## Estructura

- `dashboard/server.py` + `dashboard/index.html`: panel (solo librería estándar de Python). `start-dashboard.sh` lo lanza.
- `.env` (local, secreto): `PROXY_n` = URLs SOCKS5, `LABEL_n` opcional, `PROBE_HOST`. El panel lo escribe con permisos 600 y codifica los caracteres especiales.
- `hosts.conf` (local): `alias=usuario@ip` por VPS (usuario `wa` tras la preparación).
- `scripts/generate-compose.sh`: genera `docker-compose.yml` (una pasarela `gw-N` por `PROXY_N`).
- `scripts/prepare-vps.sh` → `bootstrap-vps.sh` (en la VPS): usuario `wa`, Docker, Tailscale, firewall, fail2ban, y orden de arranque Docker-tras-Tailscale.
- `scripts/deploy.sh`: sube compose (+ `.env` con `--env`), fija `TS_IP`, levanta y hace sondas.
- Cuenta N, en la IP de Tailscale: chat `5100+N`, medios `5200+N`, sonda `5300+N`. Los números **no se renumeran** al borrar cuentas (los puertos ya están en los iPhones).
- Clave SSH del proyecto: `~/.ssh/wa-proxy_ed25519` (la crea el panel o `prepare-vps.sh`).

## Hechos técnicos que NO debes “corregir”

- En WhatsApp el **TLS del puerto de chat debe estar APAGADO** (gost hace túnel TCP plano a `g.whatsapp.net:5222`). Con TLS encendido la app entra en bucle de reconexión.
- `.env` usa `socks5://`; `verify-proxies.sh` lo convierte a `socks5h://` y el panel resuelve el DNS en el proxy. Intencional.
- Las comillas dobles en `.env` son intencionales.
- Caracteres especiales en usuario/clave van con URL-encoding (`@`→`%40`, `:`→`%3A`, `/`→`%2F`, `#`→`%23`, `%`→`%25`); el panel lo hace solo.
- La imagen `ginuerzh/gost:2.12.0` está fijada a propósito.
- Los contenedores sin proxy fallan cerrados (no hay fuga a la IP real); no añadas rutas directas.
- `WA_BATCH=1` (lo pone el panel) desactiva preguntas y multiplexado SSH; `WA_SSH_EXTRA="-o Port=2222"` permite otro puerto SSH.

## Al modificar el repo

- Scripts en bash con `set -euo pipefail`, idempotentes, con salida `[OK]/[FALLA]`.
- Ejecuta `tests/smoke.sh` tras cambios (trabaja en una copia temporal, no toca el `.env` real).
- Para cambios en `bootstrap-vps.sh`/`prepare-vps.sh`/`deploy.sh` prueba en la VM local: `tests/vm/start-vm.sh` (ver `tests/vm/README.md`). Un contenedor o un `sshd` simulado NO basta: ya ocultó un fallo real.
- Mantén README.md y README.en.md sincronizados.
