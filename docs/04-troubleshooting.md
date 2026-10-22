# 4. Problemas frecuentes

El panel muestra los errores en texto claro. Por terminal: `./scripts/doctor.sh`, `./scripts/deploy.sh status` y `./scripts/deploy.sh probe`.

| Síntoma | Causa probable | Solución |
|---|---|---|
| Panel: «Faltan herramientas» | No hay `ssh` | Instálalo (en Windows, usa WSL) |
| Panel: «Se perdió la conexión» | Cerraste el terminal del panel | Vuelve a ejecutar `./start-dashboard.sh` y usa el enlace nuevo |
| Prueba de proxies: ❌ o «usuario o contraseña rechazados» | Datos mal escritos | Revisa servidor, puerto, usuario y contraseña con tu proveedor |
| Prueba: «el proxy no pudo conectar con g.whatsapp.net» | El proveedor bloquea ese destino | Pide al proveedor, o cambia de plan/proveedor |
| «Funciona solo por X de N IPs de la pasarela» | El proveedor tiene un nodo que no atiende tu puerto; el DNS rota y falla a ratos | Escribe a tu proveedor con la tabla de pasarelas que muestra el panel (o `./scripts/verify-proxies.sh`) |
| «Dos cuentas salen por la MISMA IP» | Dos proxies apuntan a la misma IP | Usa un puerto/IP distinto por cuenta |
| Preparar VPS: «NO se pudo entrar» | IP, usuario o contraseña incorrectos, o VPS apagada | Revisa el panel del proveedor; algunos piden **cambiar la contraseña** en el primer inicio: hazlo con `ssh root@IP` y vuelve a intentar |
| Preparar VPS se queda esperando | No autorizaste Tailscale | Pulsa el botón naranja y acepta en Tailscale (10 min de plazo) |
| Preparar VPS: «Solo se soporta Debian/Ubuntu» | La VPS usa otro sistema | Reinstala la VPS con Ubuntu 24.04 |
| VPS «Sin conexión» / «rechazó la clave» | Aún no preparada, o IP incorrecta | Usa **Preparar VPS** |
| Desplegar: «FALTA PROXY_n» | `.env` sin subir | `./scripts/deploy.sh --env` (el panel ya lo hace) |
| Cuenta «Apagada» tras un reinicio de la VPS | Tú la apagaste antes | Pulsa **Encender** |
| iPhone: conecta y se cae cada ~2 s | **TLS del chat encendido** | Apágalo en el ajuste de proxy |
| iPhone: no conecta nada | Tailscale apagado, IP o puerto equivocado | Activa Tailscale; usa la IP **100.x** y `5100+n` / `5200+n` |
| Las llamadas salen con tu IP real | Las llamadas no pasan por el proxy | Limitación conocida: no llames desde estas cuentas |

## Pedir ayuda

Abre un issue con la plantilla y **borra usuarios, contraseñas e IPs** de lo que pegues.
