# 2. Proxies SOCKS5 con IP fija

Necesitas **un proxy SOCKS5 por cada cuenta de WhatsApp**, con IP **fija** (ISP/residencial estático) y **distinta** en cada uno. Evita proxies rotativos: WhatsApp vería la IP cambiar.

## Qué pedir al proveedor

- Protocolo **SOCKS5** con usuario y contraseña.
- IP de salida fija y distinta por cuenta.
- Que permita conectar a `g.whatsapp.net` (puertos 5222 y 443) y `whatsapp.net:443`. El panel lo comprueba.

Ejemplo probado: Decodo ISP (`isp.decodo.com`), donde el **puerto** elige la IP (10001, 10002…). Sirven otros proveedores que cumplan lo anterior.

## Cargarlos

**Con el panel (`./wa dashboard`), pestaña Proxies:** escribe servidor, puerto, usuario y contraseña de cada cuenta, o pega la URL `socks5://usuario:clave@servidor:puerto`. Pulsa **Guardar** y **Probar proxies**. El panel codifica los caracteres especiales de la contraseña por ti.

**A mano:** copia `.env.example` a `.env`, rellena `PROXY_1`, `PROXY_2`… y codifica los caracteres especiales (`@`→`%40`, `:`→`%3A`, `/`→`%2F`, `#`→`%23`, `%`→`%25`, `$`→`%24`). Luego `./wa verify`.

## Qué debe salir en la prueba

La prueba comprueba **cada IP que hay detrás del nombre de tu proxy**: muchos proveedores reparten el DNS entre varias pasarelas, y si una no responde el proxy parece «intermitente».

- Cada cuenta con su **IP de salida**, todas **distintas**.
- Los tres destinos de WhatsApp en ✅.
- Si una cuenta funciona solo por **algunas** pasarelas, se marca como fallo: fallará de forma intermitente. Pide a tu proveedor que lo corrija (en la sección de soporte puedes pegar la tabla que muestra el panel).

Si algo falla: [troubleshooting](04-troubleshooting.md).

Siguiente: [3. Preparar la VPS y configurar el iPhone](03-configurar-iphone.md)
