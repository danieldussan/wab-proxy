# Lanzador para PowerShell:  .\wa.ps1 <comando>
# Usa wa.cmd (que descarga Python portable si hace falta), asi hay una sola logica.
& "$PSScriptRoot\wa.cmd" @args
exit $LASTEXITCODE
