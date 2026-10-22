# Windows

Todo funciona en **Windows 10/11** sin instalar Python ni WSL, pero esta parte **no se ha podido probar en un Windows real** (el proyecto se desarrolló y probó en Linux). Si algo falla, abre un issue con el mensaje exacto.

## Qué necesitas

| Cosa | Cómo |
|---|---|
| Este repo | *Code → Download ZIP* en GitHub y descomprime (o `git clone`) |
| **Cliente SSH** | Suele venir ya instalado. Compruébalo abriendo PowerShell y escribiendo `ssh -V`. Si no existe: *Configuración → Aplicaciones → Características opcionales → Agregar → Cliente OpenSSH* |
| Python | **No hace falta.** Si no lo tienes, el lanzador descarga una copia portable |

## Cómo se usa

- Doble clic en **`start-dashboard.cmd`**, o en CMD/PowerShell dentro de la carpeta: `.\wa.cmd dashboard`.
- Todos los comandos son iguales que en Linux cambiando `./wa` por `.\wa.cmd`: `.\wa.cmd doctor`, `.\wa.cmd verify`, `.\wa.cmd deploy`…

## Qué hace el lanzador (`wa.cmd`)

1. Si existe `.python\python.exe`, lo usa.
2. Si no, busca un Python 3.8+ instalado (`python` o `py`).
3. Si no hay ninguno, ejecuta `scripts/get-python.ps1`: descarga el *embeddable* oficial de python.org (3.12.10, ~10 MB), **comprueba su SHA256** contra el valor fijado en el script y lo descomprime en `.python\`. No requiere administrador ni toca el sistema. Para quitarlo, borra la carpeta `.python`.

## Limitaciones conocidas

- **Contraseña de root desde el panel**: usa `SSH_ASKPASS` con un pequeño `.cmd` temporal. Funciona en OpenSSH recientes, pero **no está verificado en Windows**. Alternativa segura: al crear la VPS, añade la clave SSH del panel (pestaña VPS → *Clave SSH del panel*) en el proveedor; así no hace falta contraseña. O ejecuta `.\wa.cmd prepare IP` en una terminal y escribe la contraseña cuando ssh la pida.
- **Permisos de `.env`**: en Windows no se puede garantizar el equivalente a `chmod 600`. No compartas la carpeta y no la subas a la nube sincronizada.
- Si PowerShell bloquea scripts `.ps1`, usa siempre `wa.cmd` (no los necesita).
- Antivirus: el Python portable es el oficial; si lo bloquea, instala Python desde python.org y el lanzador lo usará.
- **Alternativa: WSL.** Si prefieres, instala [WSL](https://learn.microsoft.com/windows/wsl/install) (Ubuntu) y sigue las instrucciones de Linux dentro de él. Abre el enlace del panel en el navegador de Windows (WSL2 reenvía `localhost`).
