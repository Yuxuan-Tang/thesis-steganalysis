. "$PSScriptRoot\run_hq_common.ps1"

Invoke-HqDiffStegaCase `
  -CaseName "hq_core_style_dog" `
  -ImagePath "./example/flickr_dog_000054.jpg" `
  -Prompt2 "a painting by Vincent Willem van Gogh" `
  -Pw 9000 `
  -NumSteps 30 `
  -NoiseFlip 0.05 `
  -EditStrength 0.7 `
  -RandPw

Invoke-HqDiffStegaCase `
  -CaseName "hq_core_content_boar" `
  -ImagePath "./example/000000132622.png" `
  -Prompt2 "a wild boar walking through a lush green field" `
  -Pw 1000 `
  -NumSteps 30 `
  -NoiseFlip 0.05 `
  -EditStrength 0.6

Invoke-HqDiffStegaCase `
  -CaseName "hq_core_similar_face" `
  -ImagePath "./example/00079.png" `
  -Prompt2 "a face of an old woman" `
  -Pw 2000 `
  -NumSteps 30 `
  -NoiseFlip 0.05 `
  -EditStrength 0.6
