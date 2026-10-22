# Descarga Python "embeddable" oficial (python.org) en .python\ y verifica su SHA256.
# No necesita administrador ni modifica el sistema. Solo se usa si no hay Python instalado.
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ver = "3.12.10"
$builds = @{
  "AMD64" = @{ file = "amd64"; sha = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3" }
  "ARM64" = @{ file = "arm64"; sha = "3065efc3d382d1cda66757ac71ade11904fa6e350f5a97eb74811acd71ba5532" }
  "X86"   = @{ file = "win32"; sha = "084b9eb24cb848605c895d05b738fbc2572efc8b4c18c415a824065864a2b853" }
}
$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
$b = $builds[$arch.ToUpper()]
if (-not $b) { Write-Error "Arquitectura no soportada: $arch"; exit 1 }
$root = Split-Path -Parent $PSScriptRoot
$zip = Join-Path $env:TEMP "wa-python-$ver.zip"
$url = "https://www.python.org/ftp/python/$ver/python-$ver-embed-$($b.file).zip"
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
$hash = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
if ($hash -ne $b.sha) { Remove-Item $zip -Force; Write-Error "La descarga no coincide con el SHA256 esperado. No se usará."; exit 1 }
$dest = Join-Path $root ".python"
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $dest -Force
Remove-Item $zip -Force
Write-Host "Python $ver portable listo en $dest"
