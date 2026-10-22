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

Necesitas en tu equipo **Python 3** y **ssh** (Linux, macOS, o Windows con [WSL](https://learn.microsoft.com/windows/wsl/install)).

```bash
git clone https://github.com/danieldussan/wab-proxy.git && cd wab-proxy
./start-dashboard.sh
```

Se abre una página en tu navegador (solo accesible desde tu equipo) que te guía:

1. **Tus proxies** — escribes servidor, puerto, usuario y contraseña (o pegas la URL `socks5://…`). El panel codifica los caracteres especiales por ti y puede **probar** que funcionan.
2. **Tu VPS** — escribes su IP y pulsas *Preparar* (instala Docker, Tailscale y firewall) y luego *Desplegar*.
3. **Estado y control** — ves qué cuentas están encendidas, su IP de salida, y las apagas/enciendes.
4. **iPhone** — te muestra los datos exactos para copiar y pegar en WhatsApp.

Antes necesitas comprar la VPS y los proxies → [docs/01-comprar-vps.md](docs/01-comprar-vps.md) y [docs/02-proxies.md](docs/02-proxies.md).

### Con un agente de IA

Abre Claude Code, Codex u OpenCode **dentro de esta carpeta** y pídele que te guíe: [docs/agent-prompts.md](docs/agent-prompts.md). El agente abre el panel por ti; **tú escribes las contraseñas en el panel, no en el chat**.

## Opción manual (terminal)

```bash
cp .env.example .env && chmod 600 .env     # pega tus PROXY_1, PROXY_2...
cp hosts.conf.example hosts.conf           # pon wa@IP_DE_TU_VPS
./scripts/doctor.sh                        # ¿todo listo?
./scripts/verify-proxies.sh                # prueba los proxies
./scripts/prepare-vps.sh root@IP_VPS       # solo la 1ª vez en cada VPS
./scripts/deploy.sh --env                  # despliega
```

## Puertos por cuenta

Cuenta *n* (en la IP de Tailscale de la VPS): chat `5100+n`, medios `5200+n`, sonda `5300+n`. Cuenta 1 → 5101 / 5201 / 5301, cuenta 2 → 5102 / 5202 / 5302…

## Comandos útiles

| Comando | Qué hace |
|---|---|
| `./start-dashboard.sh` | Abre el panel |
| `./scripts/doctor.sh` | Revisa el entorno local |
| `./scripts/verify-proxies.sh` | IP de salida y alcance a WhatsApp de cada proxy |
| `./scripts/prepare-vps.sh root@IP` | Prepara una VPS nueva (clave SSH, Docker, Tailscale, firewall) |
| `./scripts/deploy.sh --env` | Despliega (y sube `.env`) a todas las VPS |
| `./scripts/deploy.sh status` / `probe` / `logs gw-1` | Estado, IP de salida, logs |
| `tests/smoke.sh` | Pruebas automáticas (no necesitan VPS ni proxies reales) |
| `tests/vm/start-vm.sh` | VPS de prueba local (Ubuntu real en QEMU), para probar sin contratar nada |

## Problemas

→ [docs/04-troubleshooting.md](docs/04-troubleshooting.md)

## Seguridad

- `.env` y `hosts.conf` están en `.gitignore`. **Nunca los subas.**
- El panel solo escucha en `127.0.0.1`, exige un token aleatorio, no muestra nunca las contraseñas y solo ejecuta acciones predefinidas.
- Los puertos de los proxies solo escuchan en la IP de Tailscale; el firewall deja solo SSH público y se instala fail2ban.
- Las credenciales de los proxies son visibles con `docker inspect` en la VPS: protege el acceso a ella.

## Licencia

MIT. Proyecto independiente, sin relación con WhatsApp/Meta, Tailscale ni ningún proveedor de proxies.
