. "$PSScriptRoot\run_hq_common.ps1"

Invoke-HqDiffStegaCase -CaseName "hq_param_nf_003" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.03 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_param_nf_005" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_param_nf_008" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.08 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_param_es_050" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.5
Invoke-HqDiffStegaCase -CaseName "hq_param_es_060" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.6
Invoke-HqDiffStegaCase -CaseName "hq_param_es_070" -ImagePath "./example/00079.png" -Prompt2 "a face of an old woman" -Pw 2000 -NumSteps 30 -NoiseFlip 0.05 -EditStrength 0.7
