# Cómo funciona

```
iPhone ──Tailscale──► VPS (gost gw-n) ──SOCKS5──► proxy ISP (IP fija) ──► WhatsApp
```

Cada cuenta *n* tiene un contenedor `gw-n` con tres reenvíos TCP, todos salientes por el proxy de esa cuenta (`-F`):

| Puerto en VPS | Destino | Uso |
|---|---|---|
| `5100+n` → 5222 | `g.whatsapp.net:5222` | Chat (túnel TCP sin TLS hacia el proxy) |
| `5200+n` → 7777 | `whatsapp.net:443` | Medios (fotos, video, audios) |
| `5300+n` → 8443 | `PROBE_HOST:443` | Sonda: comprueba la IP de salida por el mismo camino |

- Los puertos se publican **solo en la IP de Tailscale** (`TS_IP`): nada queda abierto a internet.
- El DNS lo resuelve el proxy (nombre de host entregado al SOCKS5).
- Si el proxy cae, la cuenta **no conecta** (falla cerrado): no hay ruta directa.
- Tras reiniciar la VPS, Docker espera a que Tailscale tenga IP (la preparación instala esa regla de arranque) y los contenedores vuelven solos, salvo los que apagaste tú.

## Por qué gost y no el proxy oficial de WhatsApp

El proxy oficial (`facebook/whatsapp_proxy`) sirve para sortear bloqueos, no para ocultar tu IP: el backend de chat usa `send-proxy`, que añade un encabezado PROXY con la IP del cliente (en pruebas se vio la IP real del teléfono). Con gost el chat va como cliente normal desde la IP del proxy.

## Qué está probado

Probado con 3 cuentas, VPS en RackNerd, iPhone por Tailscale (Wi-Fi y datos móviles), proxies Decodo ISP:

- Texto, foto, video y notas de voz, envío y recepción, con TLS del chat apagado.
- Cada sonda devuelve la IP de salida correcta de su cuenta.
- Sin fuga al apagar el proxy (el mensaje queda pendiente; al reactivar, se envía).
- Reconexión limpia al cambiar de Wi-Fi a datos.

## Pruebas automáticas (`python tests/run_tests.py`)

Se ejecutan en una copia temporal, sin VPS ni proxies reales (usan un SOCKS5 de prueba, `tests/fake_socks5.py`):

- Generación del compose (huecos de numeración, puertos, imagen fijada).
- Panel: autenticación por token, tokens de panel y de agente separados, rechazo de Host/Origin ajenos, CSP sin `unsafe-inline`, guardado de `.env` (permisos 600, codificación de contraseñas con `@ : / #`, nunca devuelve la clave), validación de entradas, verificación de proxies (incluido el caso «solo funciona por algunas IPs de la pasarela») y VPS.
- Canal del agente (`wa agent`): pedir credenciales (la contraseña no llega al agente ni a los eventos), pedir la VPS, confirmar, rechazo (código 1), tiempo agotado (2), panel cerrado (3), y que preparar/desplegar/apagar **no se ejecutan** sin aprobar.
- Subida a la VPS con un `ssh` falso: qué archivos viajan (`docker-compose.yml`, `.env`), que `bootstrap-vps.sh` se sube y que la contraseña de root nunca aparece en la salida.

Además se probó con una **VPS simulada local** (`tests/vm/`, Ubuntu 24.04 real en QEMU/KVM con login de root por contraseña): preparación completa con contraseña desde el panel (instalación real de Docker, Tailscale, ufw y fail2ban), despliegue, sondas, apagar/encender cuentas y **reinicios de la VPS** (con la regla de arranque los contenedores vuelven con sus puertos; sin ella quedan caídos). Se repitió completa con la versión en Python y el flujo del agente (aprobación en el panel, contraseña de root vía `SSH_ASKPASS`, repetir `prepare` sin contraseña). Esa prueba encontró y corrigió un fallo silencioso de `bootstrap-vps.sh` (SIGPIPE con `pipefail`) y un enlace falso de Tailscale en el panel.

## Qué NO está verificado

- Cómo trata WhatsApp, del lado servidor, estas IPs y clientes (puede bloquear).
- Estabilidad de varias cuentas simultáneas durante muchas horas.
- Llamadas: **no** pasan por el proxy.
- Otros clientes distintos de iOS.
- La autorización real en Tailscale (se simula la IP; el panel solo captura la URL) y Debian.
- Rarezas de cada proveedor de VPS (por ejemplo, los que obligan a cambiar la contraseña en el primer inicio).
- **Windows y macOS**: se desarrolló y probó en Linux. El lanzador `wa.cmd`, el Python portable (`scripts/get-python.ps1`) y el uso de `SSH_ASKPASS` en Windows no se han podido ejecutar en un Windows real (ver [docs/05-windows.md](05-windows.md)).
