$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $root "envs\diffstega"
$env:PIP_CACHE_DIR = Join-Path $root ".cache\pip"

New-Item -ItemType Directory -Force `
  (Join-Path $root "experiments\inputs"), `
  (Join-Path $root "experiments\lsb_outputs"), `
  (Join-Path $root "experiments\analysis") `
  | Out-Null

conda run -p $envPath python (Join-Path $root "tools\create_lsb_demo_inputs.py")

conda run -p $envPath python (Join-Path $root "tools\lsb_baseline.py") `
  --cover (Join-Path $root "experiments\inputs\lsb_landscape_cover.png") `
  --secret (Join-Path $root "experiments\inputs\lsb_secret_payload.png") `
  --out-dir (Join-Path $root "experiments\lsb_outputs") `
  --name "lsb_secret_on_landscape"

conda run -p $envPath python (Join-Path $root "tools\analyze_stego_results.py") `
  --diffstega-dir (Join-Path $root "experiments\diffstega_outputs") `
  --lsb-dir (Join-Path $root "experiments\lsb_outputs") `
  --out-dir (Join-Path $root "experiments\analysis")
