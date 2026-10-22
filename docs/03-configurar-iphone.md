# 3. Preparar la VPS, desplegar y configurar el iPhone

## Con el panel (paso 2 y 3)

1. En **Tu VPS**, escribe la IP y pulsa **Añadir VPS**.
2. Abre **Preparar VPS** → escribe el usuario (`root`) y la **contraseña de root** del proveedor → **Preparar**. Tarda unos minutos.
3. Cuando aparezca el aviso naranja **«Autoriza la VPS en Tailscale»**, pulsa el botón, inicia sesión en Tailscale y acepta. El proceso continúa solo.
4. Pulsa **Desplegar proxies**. Al terminar, en **Estado y control** verás cada cuenta *Encendida* con su IP de salida (debe coincidir con la de la prueba de proxies).

## A mano

```bash
cp hosts.conf.example hosts.conf     # pon:  vps1=wa@IP_VPS
./scripts/prepare-vps.sh root@IP_VPS # solo la primera vez; pide la contraseña del proveedor y autorizar Tailscale
./scripts/deploy.sh --env
```

## En el iPhone

1. Instala **Tailscale**, inicia sesión con la **misma cuenta** que usaste en la VPS y déjalo **activado**.
2. En WhatsApp: **Ajustes → Almacenamiento y datos → Proxy → Usar proxy**.
3. Para la cuenta *n* (el paso 4 del panel te lo muestra con botones de copiar):

   | Campo | Valor |
   |---|---|
   | Dirección | IP de **Tailscale** de la VPS (100.x.x.x) |
   | Puerto de chat | `5100 + n` (cuenta 1 → 5101) |
   | Puerto de medios | `5200 + n` (cuenta 1 → 5201) |
   | **TLS del chat** | **APAGADO** |

4. Guarda y prueba texto, foto, video y nota de voz.

> **El TLS del chat debe estar apagado.** Con gost, si está encendido la app cierra la conexión a ~1 s y reintenta en bucle. El cifrado propio de WhatsApp sigue activo.

## Encender / apagar una cuenta

En el panel, **Estado y control** → *Apagar* / *Encender*. Sin proxy encendido la cuenta **no conecta** (no hay fuga a tu IP real).

A mano: `ssh wa@IP_VPS 'cd wa-proxy && docker compose stop gw-2'` (y `start`).
