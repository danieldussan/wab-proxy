# VPS de prueba local (sin pagar ni crear cuentas)

`start-vm.sh` levanta una VM **Ubuntu 24.04 real** (systemd, apt, sshd) con QEMU/KVM, con login de root por contraseña, como la que te entrega un proveedor. Sirve para probar `wa prepare`, `wa deploy` y el panel de punta a punta.

```bash
tests/vm/start-vm.sh        # primera vez descarga ~600 MB; luego arranca en segundos
tests/vm/stop-vm.sh         # apagar   (--delete borra el disco)
```

Requisitos: `qemu-system-x86_64`, `qemu-img`, `xorriso`, `curl` y acceso a `/dev/kvm` (Linux). Los pasos para usarla con el panel los imprime el propio script.

## Qué simula y qué no

| Real | Simulado |
|---|---|
| Ubuntu 24.04, systemd, `apt`, `sshd`, reinicios | La **IP de Tailscale**: no hay cuenta que autorizar, así que `tailscale ip -4` devuelve `100.64.0.1`. |
| Instalación real de Docker y de Tailscale | Esa IP aparece **25 s después de arrancar**, para comprobar que Docker espera a Tailscale. |
| Firewall `ufw`, `fail2ban`, usuario `wa` | El proxy SOCKS5: usa `tests/fake_socks5.py` (en la VM, tu equipo es `10.0.2.2`). |
| Login de root por contraseña | |

## Qué se comprobó con esta VM

- Preparar con contraseña de root (el panel la pasa por `SSH_ASKPASS`, sin guardarla), instalar Docker/Tailscale/ufw/fail2ban y que repetirlo sea idempotente.
- Desplegar, sondas, apagar/encender cuentas.
- **Reinicio de la VPS**: con la regla de espera, los contenedores vuelven con sus puertos publicados. Sin ella, quedan caídos para siempre (`failed to bind host port ...: cannot assign requested address`).

## Lo que no se puede comprobar aquí

La autorización real en Tailscale (el panel solo captura la URL), Debian, y rarezas de cada proveedor (p. ej. los que obligan a cambiar la contraseña en el primer login).
