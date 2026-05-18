$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:HF_HOME = Join-Path $root ".cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $root ".cache\huggingface\hub"
$env:TORCH_HOME = Join-Path $root ".cache\torch"
$env:PIP_CACHE_DIR = Join-Path $root ".cache\pip"
$env:CONDA_PKGS_DIRS = Join-Path $root ".cache\conda_pkgs"

New-Item -ItemType Directory -Force `
  $env:HF_HOME, $env:HUGGINGFACE_HUB_CACHE, $env:TORCH_HOME, $env:PIP_CACHE_DIR, $env:CONDA_PKGS_DIRS `
  | Out-Null

$envPath = Join-Path $root "envs\diffstega"

if (-not (Test-Path $envPath)) {
  conda create -p $envPath python=3.11.5 -y
}

conda run -p $envPath python -m pip install --upgrade pip
conda install -p $envPath pytorch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 pytorch-cuda=12.1 -c pytorch -c nvidia -y
conda run -p $envPath python -m pip install diffusers==0.26.3 accelerate==0.23.0 transformers==4.38.2 huggingface_hub==0.20.2 controlnet_aux==0.0.7 opencv-python pyyaml tqdm
conda run -p $envPath python -m pip install -r (Join-Path $root "requirements-analysis.txt")

conda run -p $envPath python -c "import torch; print('torch', torch.__version__); print('cuda available', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
