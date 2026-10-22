# AGENTS.md — guía para agentes de IA (Claude Code, Codex, OpenCode…)

Objetivo: ayudar a una persona (probablemente **no técnica**) a dejar funcionando proxies de WhatsApp **por cuenta** en una VPS. Responde en el idioma del usuario, explica cada paso en una frase y verifica antes de avanzar.

## Cómo trabajas: el panel es tu canal con el usuario

El repo trae un panel web local. El usuario lo ve en su navegador y **ve en directo lo que haces**. Todo lo que necesite de él (credenciales, permisos) se lo pides **por el panel, nunca por el chat**.

Lanzador: `./wa …` (Linux/macOS) o `.\wa.cmd …` (Windows). Abajo se escribe `wa`.

1. `wa doctor` — comprueba lo básico (Python y `ssh`).
2. `wa agent open` — abre el panel en el navegador del usuario (lo arranca si hace falta). No imprime el enlace con el token. Si el agente corre en otra máquina (nube/SSH), el usuario debe abrir un túnel y ejecutar `wa dashboard` él mismo.
3. Avisa al usuario de que mire el panel y guíalo con el banner «Siguiente paso» del *Resumen*.
4. Mantén el panel informado:
   - `wa agent say "Voy a probar tus proxies"` → aparece en *Actividad*.
   - `wa agent working "Desplegando…"` → se muestra en la barra superior; `wa agent working --done` al terminar.

## Protocolo `wa agent` (todo lo que toca al usuario pasa por aquí)

| Necesitas… | Comando | Qué ve el usuario |
|---|---|---|
| Credenciales de un proxy | `wa agent ask-proxy [--n N] [--label Ventas] [--message "…"]` | Formulario (servidor, puerto, usuario, contraseña o pegar URL `socks5://`). Se guarda en `.env`. **Tú solo recibes «guardado»**, nunca la contraseña. |
| La VPS | `wa agent ask-vps [--message "…"]` | Formulario con IP y nombre. |
| Un sí/no | `wa agent confirm "¿…?"` | Ventana con Aceptar / Rechazar. |
| Probar proxies | `wa agent run verify` | Se ejecuta sin pedir permiso (no cambia nada). Imprime `[OK]`/`[FALLA]` por cuenta. |
| Preparar la VPS | `wa agent run prepare [--alias vps1]` | **Pide aprobación.** En la ventana el usuario escribe la contraseña de root del proveedor (se usa una vez, no se guarda y no llega hasta ti). |
| Desplegar | `wa agent run deploy [--alias vps1]` | **Pide aprobación.** |
| Encender/apagar/reiniciar una cuenta | `wa agent run power --alias vps1 --n 2 --do stop` (`start`\|`stop`\|`restart`) | **Pide aprobación.** |
| Estado de la VPS | `wa agent status [--alias vps1]` | Nada (solo lectura): contenedores, IP de salida, IP de Tailscale. |
| Resumen sin secretos | `wa agent state` | Nada. |

Códigos de salida: `0` bien · `1` el usuario rechazó o la acción falló · `2` el usuario no respondió a tiempo (`--timeout`, 900 s por defecto) · `3` el panel no está abierto (`wa agent open`). Si recibes `1` por rechazo, **no insistas ni lo intentes por otra vía**: pregunta al usuario qué prefiere.

`prepare` pide además autorizar la VPS en Tailscale: el panel detecta la URL en la consola y le muestra un botón al usuario. Espera a que termine.

## Reglas de seguridad (obligatorias)

1. **Nunca leas, imprimas ni pegues el contenido de `.env`, `hosts.conf` ni `.wa-session.json`.** Para revisarlos usa `wa doctor` y `wa agent state`. Para confirmar una variable: `grep -c '^PROXY_1=' .env`, nunca `cat`.
2. **No uses los comandos locales que modifican la VPS (`wa prepare`, `wa deploy`) ni `ssh` directo.** Usa `wa agent run …` para que el usuario lo apruebe. Esos comandos directos son para que los ejecute la persona en su terminal.
3. **Nunca hagas commit de `.env`, `hosts.conf`, `docker-compose.yml` ni `.wa-session.json`** (están en `.gitignore`; no uses `git add -f`).
4. Si el usuario pega credenciales en el chat, avísale de que debe rotarlas y que las escriba solo en el panel.
5. No abras puertos al público. Todo escucha solo en la IP de Tailscale. No cambies el firewall salvo petición explícita.
6. No prometas que WhatsApp no bloqueará las cuentas. Recuerda: números de prueba, y las llamadas NO pasan por el proxy.
7. No cambies el panel para que escuche fuera de `127.0.0.1`, devuelva contraseñas, ejecute comandos arbitrarios o relaje la CSP.

Límite honesto del diseño: el token del agente (`.wa-session.json`) evita errores y acciones sin permiso, pero un agente con acceso total al terminal podría leer `.env`. Por eso la regla 1 es una regla de conducta, no una barrera técnica.

## Flujo completo

| # | Paso | Con el agente | Éxito si |
|---|---|---|---|
| 0 | Entorno | `wa doctor` + `wa agent open` | `[OK]` y panel abierto |
| 1 | Proxies | `wa agent ask-proxy` (una vez por cuenta) → `wa agent run verify` | `[OK]` en todas, IPs distintas |
| 2 | VPS | `wa agent ask-vps` → `wa agent run prepare` | termina en `PREPARACIÓN COMPLETA` |
| 3 | Desplegar | `wa agent run deploy` → `wa agent status` | contenedores `running` y sondas con las IPs esperadas |
| 4 | iPhone | `docs/03-configurar-iphone.md` (el panel muestra los datos en la pestaña *iPhone*) | mensajes, fotos y audio funcionan |

Diagnóstico: `wa agent status`, `wa doctor` y `docs/04-troubleshooting.md`.

## Estructura

- `wa_proxy/`: paquete Python (solo librería estándar). `core.py` (lógica: `.env`, compose, verificación SOCKS5, SSH, prepare, deploy), `dashboard.py` (servidor del panel y endpoints `/agent/*`), `agent.py` (cliente `wa agent`), `cli.py`. UI en `wa_proxy/static/` (`index.html`, `app.js`, `app.css`, `icons.js` con iconos de Lucide, licencia ISC).
- `wa`, `wa.cmd`, `wa.ps1`, `wa.py`: lanzadores. `wa.cmd` descarga un Python portable en `.python/` si no hay Python (`scripts/get-python.ps1`).
- `scripts/bootstrap-vps.sh`: lo único en bash. Se ejecuta **en la VPS** (usuario `wa`, Docker, Tailscale, firewall, fail2ban, y orden de arranque Docker-tras-Tailscale).
- `.env` (local, secreto): `PROXY_n` = URLs SOCKS5, `LABEL_n` opcional, `PROBE_HOST`. Se escribe con permisos 600 y codifica los caracteres especiales.
- `hosts.conf` (local): `alias=usuario@ip` por VPS (usuario `wa` tras la preparación).
- `.wa-session.json` (local, 600): puerto y **token del agente** del panel en marcha. El token del panel solo vive en memoria y en el enlace que abre el usuario.
- Cuenta N, en la IP de Tailscale: chat `5100+N`, medios `5200+N`, sonda `5300+N`. Los números **no se renumeran** al borrar cuentas (los puertos ya están en los iPhones).
- Clave SSH del proyecto: `~/.ssh/wa-proxy_ed25519` (la crea el panel o `wa prepare`).

## Hechos técnicos que NO debes “corregir”

- En WhatsApp el **TLS del puerto de chat debe estar APAGADO** (gost hace túnel TCP plano a `g.whatsapp.net:5222`). Con TLS encendido la app entra en bucle de reconexión.
- `.env` usa `socks5://`; la verificación pasa el nombre al proxy (DNS en el proxy). Intencional.
- La verificación prueba **cada** IP detrás del nombre del proxy: si solo algunas funcionan, es fallo («parcial»), porque el DNS rota y fallaría a ratos.
- Las comillas dobles en `.env` son intencionales.
- Caracteres especiales en usuario/clave van con URL-encoding (`@`→`%40`, `:`→`%3A`, `/`→`%2F`, `#`→`%23`, `%`→`%25`); el panel lo hace solo.
- La imagen `ginuerzh/gost:2.12.0` está fijada a propósito.
- Los contenedores sin proxy fallan cerrados (no hay fuga a la IP real); no añadas rutas directas.
- SSH: no se usa `ControlMaster` (cuelga con salida redirigida y no existe en Windows). Los scripts remotos viajan por stdin (`bash -s`). `WA_SSH_EXTRA="-o Port=2222"` permite otro puerto SSH; `WA_SSH_KEY` otra clave; `WA_ROOT` otra carpeta de datos (lo usan los tests).

## Al modificar el repo

- Python 3.8+ solo con librería estándar; que funcione en Linux, macOS y Windows (sin rutas con `/` fijas, sin `fork`, `chmod` tolerante, `.cmd` con saltos CRLF).
- La UI no usa `innerHTML` ni estilos/scripts en línea (CSP estricta); los textos salen siempre en ES y EN (`I18N` en `app.js`).
- Ejecuta `python tests/run_tests.py` tras cambios (usa una carpeta temporal, no toca el `.env` real).
- Para cambios en `bootstrap-vps.sh` o en `prepare`/`deploy` prueba en la VM local: `tests/vm/start-vm.sh` (ver `tests/vm/README.md`). Un contenedor o un `sshd` simulado NO basta: ya ocultó un fallo real.
- Mantén README.md y README.en.md sincronizados.
