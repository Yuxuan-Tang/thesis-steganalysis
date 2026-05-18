. "$PSScriptRoot\run_hq_common.ps1"

$env:PYTHONIOENCODING = "utf-8"
& (Join-Path $script:EnvPath "python.exe") (Join-Path $PSScriptRoot "tools\prepare_hq_ext_inputs.py")
if ($LASTEXITCODE -ne 0) {
  throw "Failed to prepare HQ extension inputs"
}

$cases = @(
  @{Name="hq_ext_sk_astronaut"; Image="../experiments/inputs_hq_ext/sk_astronaut.png"; Prompt="a portrait of an astronaut in a space suit"; Pw=6101},
  @{Name="hq_ext_sk_coffee"; Image="../experiments/inputs_hq_ext/sk_coffee.png"; Prompt="a cup of coffee on a table"; Pw=6102},
  @{Name="hq_ext_sk_rocket"; Image="../experiments/inputs_hq_ext/sk_rocket.png"; Prompt="a rocket launching into the sky"; Pw=6103},
  @{Name="hq_ext_sk_cat"; Image="../experiments/inputs_hq_ext/sk_cat.png"; Prompt="a cat sitting indoors"; Pw=6104},
  @{Name="hq_ext_sk_camera"; Image="../experiments/inputs_hq_ext/sk_camera.png"; Prompt="a portrait photograph of a person"; Pw=6105},
  @{Name="hq_ext_sk_horse"; Image="../experiments/inputs_hq_ext/sk_horse.png"; Prompt="a black horse in a natural scene"; Pw=6106},
  @{Name="hq_ext_sk_hubble"; Image="../experiments/inputs_hq_ext/sk_hubble.png"; Prompt="a deep space galaxy field"; Pw=6107},
  @{Name="hq_ext_sk_retina"; Image="../experiments/inputs_hq_ext/sk_retina.png"; Prompt="a close-up photograph of an eye"; Pw=6108},
  @{Name="hq_ext_pw_face_3001"; Image="./example/00079.png"; Prompt="a face of an old woman"; Pw=3001},
  @{Name="hq_ext_pw_face_3002"; Image="./example/00079.png"; Prompt="a face of an old woman"; Pw=3002},
  @{Name="hq_ext_pw_boar_4001"; Image="./example/000000132622.png"; Prompt="a wild boar walking through a lush green field"; Pw=4001},
  @{Name="hq_ext_pw_boar_4002"; Image="./example/000000132622.png"; Prompt="a wild boar walking through a lush green field"; Pw=4002},
  @{Name="hq_ext_pw_dog_5001"; Image="./example/flickr_dog_000054.jpg"; Prompt="a painting by Vincent Willem van Gogh"; Pw=5001; Edit=0.7},
  @{Name="hq_ext_pw_dog_5002"; Image="./example/flickr_dog_000054.jpg"; Prompt="a painting by Vincent Willem van Gogh"; Pw=5002; Edit=0.7}
)

foreach ($case in $cases) {
  $editStrength = if ($case.ContainsKey("Edit")) { [double]$case.Edit } else { 0.6 }
  Invoke-HqDiffStegaCase `
    -CaseName $case.Name `
    -ImagePath $case.Image `
    -Prompt2 $case.Prompt `
    -Pw ([int]$case.Pw) `
    -NumSteps 30 `
    -FallbackNumSteps 20 `
    -NoiseFlip 0.05 `
    -EditStrength $editStrength `
    -OutputSubdir "diffstega_outputs_hq_ext"
}
