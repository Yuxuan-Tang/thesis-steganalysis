$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $root "envs\diffstega"

conda run -p $envPath python (Join-Path $root "tools\analyze_hq_results.py") `
  --diffstega-dir (Join-Path $root "experiments\diffstega_outputs_hq") `
  --out-dir (Join-Path $root "experiments\analysis_hq")
