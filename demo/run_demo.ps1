$ErrorActionPreference = 'Stop'
$demoPath = Join-Path $PSScriptRoot 'Home.py'
& python -m streamlit run $demoPath --server.address localhost
exit $LASTEXITCODE
