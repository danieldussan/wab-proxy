# 1. Comprar la VPS

Una VPS es un computador alquilado que está siempre encendido. Aquí correrán tus proxies.

## Qué comprar

| Recurso | Mínimo | Nota |
|---|---|---|
| Sistema | **Ubuntu 22.04 / 24.04 o Debian 12** | Es lo único soportado |
| RAM | 512 MB (1 GB recomendado) | cada cuenta usa ~30 MB |
| CPU / disco | 1 vCPU / 10 GB | sobra |
| Red | IPv4 pública | |

Sirve la VPS más barata de cualquier proveedor (RackNerd, Hetzner, DigitalOcean, Vultr…). **La IP de la VPS no es la que ve WhatsApp** (esa es la del proxy), así que su ubicación importa poco.

## Al crearla

1. Elige **Ubuntu 24.04** (o Debian 12).
2. Anota la **IP** y la **contraseña de root** que te da el proveedor (casi todos te la envían por correo o la muestran en su panel). El panel la usa **una sola vez** y no la guarda.
   - Si tu proveedor te deja añadir una clave SSH al crearla, puedes pegar la del panel (sección «Clave SSH del panel» en el paso 2) y no necesitarás contraseña.
3. Comprueba que la VPS esté **encendida** en el panel del proveedor.

## También necesitas

- Una cuenta gratuita en [Tailscale](https://tailscale.com). Se usa la **misma cuenta** en la VPS y en el iPhone.
- En tu equipo: **ssh** (en Windows 10/11 ya viene) y **Python 3** en Linux/macOS (en Windows el lanzador lo descarga solo; ver [05-windows.md](05-windows.md)).

Siguiente: [2. Proxies](02-proxies.md)
