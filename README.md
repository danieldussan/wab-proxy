# WhatsApp Proxy por cuenta (VPS + Tailscale + gost)

🇪🇸 Español · [🇬🇧 English](README.en.md)

Cada cuenta de WhatsApp (por ejemplo, un duplicado en iPhone) sale a internet por **una IP fija distinta**, a través de tu propia VPS. Cada cuenta tiene su pasarela [gost](https://github.com/ginuerzh/gost) en Docker y se enciende o apaga por separado.

```
iPhone (WhatsApp → Ajustes → Proxy)
   │  por Tailscale (VPN privada)
   ▼
Tu VPS ── contenedor gost por cuenta ──► proxy SOCKS5 (IP fija) ──► WhatsApp
```

> ⚠️ **Lee esto primero**
> - Es un experimento. WhatsApp puede bloquear clientes modificados o IPs de proxy. **Usa números de prueba, no cuentas importantes.**
> - **Las llamadas no pasan por el proxy** y saldrían con tu IP real. No uses llamadas en estas cuentas.
> - Este repo no te da proxies ni servidor: tú compras los proxies SOCKS5 con IP fija y una VPS.
> - Qué está probado y qué no: [cómo funciona](docs/how-it-works.md#qué-está-probado).

## Opción recomendada: con el panel (sin saber de terminal)

**Linux / macOS** (necesitas `python3` y `ssh`, que casi siempre ya vienen):

```bash
git clone https://github.com/danieldussan/wab-proxy.git && cd wab-proxy
./wa dashboard
```

**Windows 10/11**: descarga el repo (botón *Code → Download ZIP*, o `git clone`), descomprímelo y haz **doble clic en `start-dashboard.cmd`** (o escribe `.\wa.cmd dashboard` en PowerShell/CMD dentro de la carpeta). **No hace falta instalar Python**: la primera vez el lanzador baja una copia portable (~10 MB, verificada) a la carpeta `.python`. Solo necesitas el cliente SSH de Windows, que suele venir ya instalado → [docs/05-windows.md](docs/05-windows.md).

Se abre una página en tu navegador (solo accesible desde tu equipo) que te guía:

1. **Proxies** — escribes servidor, puerto, usuario y contraseña (o pegas la URL `socks5://…`). El panel codifica los caracteres especiales por ti y puede **probar** que funcionan.
2. **VPS** — escribes su IP y pulsas *Preparar* (instala Docker, Tailscale y firewall) y luego *Desplegar*.
3. **Cuentas** — ves qué cuentas están encendidas, su IP de salida, y las apagas/enciendes.
4. **iPhone** — te muestra los datos exactos para copiar y pegar en WhatsApp.

El **Resumen** te dice siempre cuál es el siguiente paso. Antes necesitas comprar la VPS y los proxies → [docs/01-comprar-vps.md](docs/01-comprar-vps.md) y [docs/02-proxies.md](docs/02-proxies.md).

### Con un agente de IA

Abre Claude Code, Codex u OpenCode **dentro de esta carpeta** y pídele que te guíe: [docs/agent-prompts.md](docs/agent-prompts.md). El agente abre el panel por ti y **ves en directo lo que hace** (columna *Actividad* y *Consola*). Cuando necesita algo de ti, te lo pide **en el panel**:

- **Credenciales** (proxy, contraseña de root): las escribes en una ventana del panel y se guardan solo en tu equipo. **El agente nunca las ve ni pasan por el chat.**
- **Permisos**: para preparar la VPS, desplegar o apagar/encender una cuenta, el agente tiene que pedírtelo y tú pulsas *Permitir*.

## Opción manual (terminal)

```bash
./wa dashboard --no-open                   # (opcional) o edita los archivos a mano:
cp .env.example .env && chmod 600 .env     # pega tus PROXY_1, PROXY_2...
cp hosts.conf.example hosts.conf           # pon wa@IP_DE_TU_VPS
./wa doctor                                # ¿todo listo?
./wa verify                                # prueba los proxies
./wa prepare IP_VPS                        # solo la 1ª vez en cada VPS (usuario root)
./wa deploy                                # despliega
```

En Windows usa `.\wa.cmd` en vez de `./wa` (funciona en CMD y en PowerShell).

## Puertos por cuenta

Cuenta *n* (en la IP de Tailscale de la VPS): chat `5100+n`, medios `5200+n`, sonda `5300+n`. Cuenta 1 → 5101 / 5201 / 5301, cuenta 2 → 5102 / 5202 / 5302…

## Comandos útiles

| Comando | Qué hace |
|---|---|
| `./wa dashboard` | Abre el panel |
| `./wa doctor` | Revisa el entorno local |
| `./wa verify` | IP de salida y alcance a WhatsApp de cada proxy (por **cada** IP de la pasarela del proveedor) |
| `./wa prepare IP` | Prepara una VPS nueva (clave SSH, Docker, Tailscale, firewall) |
| `./wa deploy` | Despliega (y sube `.env`) a todas las VPS (`-t alias` para una sola) |
| `./wa status` / `probe` / `logs gw-1` | Estado, IP de salida, logs |
| `./wa agent --help` | Canal para agentes de IA ([AGENTS.md](AGENTS.md)) |
| `python tests/run_tests.py` | Pruebas automáticas (no necesitan VPS ni proxies reales) |
| `tests/vm/start-vm.sh` | VPS de prueba local (Ubuntu real en QEMU), para probar sin contratar nada |

## Problemas

→ [docs/04-troubleshooting.md](docs/04-troubleshooting.md)

## Seguridad

- `.env` y `hosts.conf` están en `.gitignore`. **Nunca los subas.**
- El panel solo escucha en `127.0.0.1`, exige un token aleatorio, no muestra nunca las contraseñas, aplica una política CSP estricta y solo ejecuta acciones predefinidas.
- El agente de IA usa un token **distinto** al del panel y no puede preparar/desplegar/apagar sin que lo apruebes. Límite honesto: esto protege contra errores y malentendidos, no contra un agente malicioso con acceso total a tu terminal (podría leer `.env`). Usa solo agentes en los que confíes.
- Las contraseñas de `.env` quedan en texto plano en tu equipo (hace falta para Docker) con permisos 600 en Linux/macOS; en Windows ese permiso no se puede garantizar.
- Los puertos de los proxies solo escuchan en la IP de Tailscale; el firewall deja solo SSH público y se instala fail2ban.
- Las credenciales no salen en `docker inspect`, `ps` ni `docker compose config`: gost las lee de `~/wa-proxy/conf/` (carpeta 700), que se genera en la VPS desde su `.env`. Quien sea root en la VPS sí puede leerlas: protege el acceso a ella. Los contenedores corren con `read_only`, sin capacidades y con límite de memoria.

## Licencia

MIT. Proyecto independiente, sin relación con WhatsApp/Meta, Tailscale ni ningún proveedor de proxies.
