param(
    [switch]$CopySo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$here = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Set-Location $here

if (-not (Get-Command gcc -ErrorAction SilentlyContinue)) {
    throw "gcc não encontrado no PATH. Instale o Mingw-w64/LLVM ou adicione gcc ao PATH."
}

if (Test-Path build) {
    Remove-Item build -Recurse -Force
}
New-Item -ItemType Directory -Path build | Out-Null

$sources = @(
    "src/graph.c",
    "src/dijkstra.c",
    "src/yen.c",
    "src/edge_analysis.c"
)

$args = @(
    "-O3",
    "-DNDEBUG",
    "-Wall",
    "-Wextra",
    "-I./src",
    "-shared",
    "-DCONNEC_BUILD",
    "-o", "build/libconneccity.dll"
)

& gcc @args $sources

Write-Host "✔ libconneccity.dll gerada em $(Join-Path $here 'build/libconneccity.dll')"

if ($CopySo) {
    Copy-Item build/libconneccity.dll build/libconneccity.so -Force
    Write-Host "✔ libconneccity.so copiada para compatibilidade com ffi"
}

Write-Host "Pronto. Configure a API para carregar 'build/libconneccity.dll' ao rodar no Windows."

