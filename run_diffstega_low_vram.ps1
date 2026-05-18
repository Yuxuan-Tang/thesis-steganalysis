$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $root "DiffStega"
$envPath = Join-Path $root "envs\diffstega"

$env:HF_HOME = Join-Path $root ".cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $root ".cache\huggingface\hub"
$env:TORCH_HOME = Join-Path $root ".cache\torch"
$env:PIP_CACHE_DIR = Join-Path $root ".cache\pip"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:64"

New-Item -ItemType Directory -Force (Join-Path $root "experiments\diffstega_outputs") | Out-Null

Push-Location $repo
try {
  conda run -p $envPath python main.py `
    --image_path ./example/flickr_dog_000054.jpg `
    --prompt2 "a painting by Vincent Willem van Gogh" `
    --save_path ../experiments/diffstega_outputs/style_dog `
    --optional_control none `
    --edit_strength 0.7 `
    --num_steps 10 `
    --low_vram `
    --single_model `
    --rand_pw

  conda run -p $envPath python main.py `
    --image_path ./example/000000132622.png `
    --prompt2 "a wild boar walking through a lush green field" `
    --save_path ../experiments/diffstega_outputs/content_boar `
    --optional_control none `
    --edit_strength 0.6 `
    --num_steps 10 `
    --low_vram `
    --single_model `
    --pw 1000

  conda run -p $envPath python main.py `
    --image_path ./example/00079.png `
    --prompt2 "a face of an old woman" `
    --save_path ../experiments/diffstega_outputs/similar_face `
    --optional_control none `
    --edit_strength 0.6 `
    --num_steps 10 `
    --low_vram `
    --single_model `
    --pw 2000
}
finally {
  Pop-Location
}
