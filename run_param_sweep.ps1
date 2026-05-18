$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $root "DiffStega"
$envPath = Join-Path $root "envs\diffstega"

$env:HF_HOME = Join-Path $root ".cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $root ".cache\huggingface\hub"
$env:TORCH_HOME = Join-Path $root ".cache\torch"
$env:PIP_CACHE_DIR = Join-Path $root ".cache\pip"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:64"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

New-Item -ItemType Directory -Force (Join-Path $root "experiments\diffstega_outputs") | Out-Null

function Test-CaseComplete {
  param([string]$SavePath)
  if (-not (Test-Path $SavePath)) {
    return $false
  }
  $correct = Get-ChildItem -Path $SavePath -Filter "*_rec_w_*.png" -ErrorAction SilentlyContinue
  $wrong = Get-ChildItem -Path $SavePath -Filter "*_rec_wo_*.png" -ErrorAction SilentlyContinue
  return (($correct.Count -gt 0) -and ($wrong.Count -gt 0))
}

function Invoke-ParamCase {
  param(
    [string]$CaseName,
    [double]$NoiseFlip,
    [double]$EditStrength
  )

  $savePath = Join-Path $root "experiments\diffstega_outputs\$CaseName"
  if (Test-CaseComplete -SavePath $savePath) {
    Write-Host "Skip completed case: $CaseName"
    return
  }

  Write-Host "Running $CaseName noise_flip_scale=$NoiseFlip edit_strength=$EditStrength"
  New-Item -ItemType Directory -Force $savePath | Out-Null

  Push-Location $repo
  try {
    conda run -p $envPath python main.py `
      --image_path ./example/00079.png `
      --prompt2 "a face of an old woman" `
      --save_path "../experiments/diffstega_outputs/$CaseName" `
      --optional_control none `
      --noise_flip_scale $NoiseFlip `
      --edit_strength $EditStrength `
      --num_steps 10 `
      --low_vram `
      --single_model `
      --pw 2000
    if ($LASTEXITCODE -ne 0) {
      throw "DiffStega failed for $CaseName with exit code $LASTEXITCODE"
    }
  }
  finally {
    Pop-Location
  }
}

Invoke-ParamCase -CaseName "param_nf_003" -NoiseFlip 0.03 -EditStrength 0.6
Invoke-ParamCase -CaseName "param_nf_005" -NoiseFlip 0.05 -EditStrength 0.6
Invoke-ParamCase -CaseName "param_nf_008" -NoiseFlip 0.08 -EditStrength 0.6
Invoke-ParamCase -CaseName "param_es_050" -NoiseFlip 0.05 -EditStrength 0.5
Invoke-ParamCase -CaseName "param_es_060" -NoiseFlip 0.05 -EditStrength 0.6
Invoke-ParamCase -CaseName "param_es_070" -NoiseFlip 0.05 -EditStrength 0.7

Write-Host "Parameter sweep finished."
