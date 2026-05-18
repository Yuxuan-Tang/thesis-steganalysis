. "$PSScriptRoot\run_hq_common.ps1"

Invoke-HqDiffStegaCase `
  -CaseName "hq_calib_steps_30" `
  -ImagePath "./example/00079.png" `
  -Prompt2 "a face of an old woman" `
  -Pw 2000 `
  -NumSteps 30 `
  -NoiseFlip 0.05 `
  -EditStrength 0.6

Invoke-HqDiffStegaCase `
  -CaseName "hq_calib_steps_50" `
  -ImagePath "./example/00079.png" `
  -Prompt2 "a face of an old woman" `
  -Pw 2000 `
  -NumSteps 50 `
  -NoiseFlip 0.05 `
  -EditStrength 0.6
