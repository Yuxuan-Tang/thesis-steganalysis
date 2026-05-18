$ErrorActionPreference = "Stop"

$script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:Repo = Join-Path $script:Root "DiffStega"
$script:EnvPath = Join-Path $script:Root "envs\diffstega"

$env:HF_HOME = Join-Path $script:Root ".cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $script:Root ".cache\huggingface\hub"
$env:TORCH_HOME = Join-Path $script:Root ".cache\torch"
$env:PIP_CACHE_DIR = Join-Path $script:Root ".cache\pip"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:64"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

New-Item -ItemType Directory -Force (Join-Path $script:Root "experiments\diffstega_outputs_hq") | Out-Null

function Test-HqCaseComplete {
  param([string]$SavePath)
  if (-not (Test-Path $SavePath)) {
    return $false
  }
  $secret = Get-ChildItem -Path $SavePath -Filter "*.png" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '_(hide|rec|ref|wrg)_' }
  $hide = Get-ChildItem -Path $SavePath -Filter "*_hide_pw_*.png" -ErrorAction SilentlyContinue
  $correct = Get-ChildItem -Path $SavePath -Filter "*_rec_w_*.png" -ErrorAction SilentlyContinue
  $wrong = Get-ChildItem -Path $SavePath -Filter "*_rec_wo_*.png" -ErrorAction SilentlyContinue
  return (($secret.Count -gt 0) -and ($hide.Count -gt 0) -and ($correct.Count -gt 0) -and ($wrong.Count -gt 0))
}

function Invoke-HqDiffStegaCase {
  param(
    [string]$CaseName,
    [string]$ImagePath,
    [string]$Prompt2,
    [int]$Pw,
    [int]$NumSteps,
    [double]$NoiseFlip = 0.05,
    [double]$EditStrength = 0.6,
    [switch]$RandPw,
    [string]$OutputSubdir = "diffstega_outputs_hq",
    [int]$FallbackNumSteps = 0
  )

  $savePath = Join-Path $script:Root "experiments\$OutputSubdir\$CaseName"
  if (Test-HqCaseComplete -SavePath $savePath) {
    Write-Host "Skip completed HQ case: $CaseName"
    return
  }

  Write-Host "Running HQ case: $CaseName steps=$NumSteps noise_flip_scale=$NoiseFlip edit_strength=$EditStrength output=$OutputSubdir"
  New-Item -ItemType Directory -Force $savePath | Out-Null

  function Invoke-Once {
    param([int]$Steps)
    $args = @(
      "main.py",
      "--image_path", $ImagePath,
      "--prompt2", $Prompt2,
      "--save_path", "../experiments/$OutputSubdir/$CaseName",
      "--optional_control", "none",
      "--noise_flip_scale", "$NoiseFlip",
      "--edit_strength", "$EditStrength",
      "--num_steps", "$Steps",
      "--low_vram",
      "--single_model"
    )
    if ($RandPw) {
      $args += "--rand_pw"
    } else {
      $args += @("--pw", "$Pw")
    }
    conda run -p $script:EnvPath python @args
    return $LASTEXITCODE
  }

  Push-Location $script:Repo
  try {
    $exitCode = Invoke-Once -Steps $NumSteps
    if (($exitCode -ne 0) -and ($FallbackNumSteps -gt 0)) {
      Write-Warning "DiffStega failed for $CaseName at $NumSteps steps, retrying with $FallbackNumSteps steps"
      $exitCode = Invoke-Once -Steps $FallbackNumSteps
    }
    if ($exitCode -ne 0) {
      $logPath = Join-Path $script:Root "experiments\$OutputSubdir\failed_cases.log"
      Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format s) $CaseName failed with exit code $exitCode"
      Write-Warning "DiffStega failed for $CaseName with exit code $exitCode; recorded and continuing"
      return
    }
    if (-not (Test-HqCaseComplete -SavePath $savePath)) {
      $logPath = Join-Path $script:Root "experiments\$OutputSubdir\failed_cases.log"
      Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format s) $CaseName finished but output set is incomplete"
      Write-Warning "DiffStega output incomplete for $CaseName; recorded and continuing"
      return
    }
  }
  finally {
    Pop-Location
  }
}
