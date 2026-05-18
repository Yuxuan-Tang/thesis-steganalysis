. "$PSScriptRoot\run_hq_common.ps1"

Invoke-HqDiffStegaCase -CaseName "hq_prompt_similar" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_prompt_style" -ImagePath "./example/00079.png" -Prompt2 "a portrait painting in oil painting style" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_prompt_weak" -ImagePath "./example/00079.png" -Prompt2 "a person in a city street" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_prompt_unrelated" -ImagePath "./example/00079.png" -Prompt2 "a mountain landscape at sunset" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
