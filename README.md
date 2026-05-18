# thesis-steganalysis

## 项目声明

- 项目名称：面向抗隐写分析的生成式无载体图像隐写安全性评估研究
- 项目作者：唐宇轩
- 作者单位：网络空间安全学院
- 开发语言：Python、PowerShell
- 框架：PyTorch、Diffusers（依赖第三方 DiffStega 项目）
- 核心技术：生成式无载体图像隐写安全性评估、LSB 对照实验、图像质量指标、轻量隐写分析

本科毕业设计配套代码与实验材料：
《面向抗隐写分析的生成式无载体图像隐写安全性评估研究》。

本仓库只包含本人围绕毕业设计整理的实验运行脚本、轻量化隐写分析工具、传统 LSB 对照基线、统计分析代码、结果样例与复现实验说明。第三方 DiffStega 源码、模型权重、虚拟环境、缓存和大批量原始输出不包含在本仓库中。

## 研究内容

本项目基于公开的 DiffStega 生成式无载体图像隐写框架，设计一套轻量化安全性评估流程，从以下角度对结果进行分析：

- 正确密钥与错误密钥恢复差异；
- 生成式隐写结果的图像质量与自然性；
- LSB 修改式隐写基线的像素残差、直方图与统计特征；
- 参数变化对隐蔽性、恢复质量和密钥区分度的影响；
- 面向低显存设备的可复现实验流程。

## 目录结构

```text
.
+-- tools/                         # 本人编写的分析、基线和结果整理脚本
+-- experiments/
|   +-- analysis_samples/           # 少量代表性图表与指标样例
|   +-- analysis_hq_combined/       # 高质量实验汇总 CSV
|   +-- analysis_steganalysis/      # 轻量隐写分析统计结果
+-- thesis_materials/               # 实验说明、论文表述和答辩辅助材料
+-- run_*.ps1                       # Windows PowerShell 复现实验脚本
+-- setup_diffstega_env.ps1         # 本地实验环境初始化脚本
+-- requirements-analysis.txt       # 分析脚本依赖
+-- LICENSE                         # 本仓库自研部分的 MIT 许可证
```

## 第三方依赖说明

本仓库不再分发 DiffStega 源码和模型权重。若需要完整复现实验，请另行获取第三方项目：

- DiffStega: <https://github.com/evtricks/DiffStega>
- IP-Adapter 模型权重: <https://huggingface.co/h94/IP-Adapter>

建议将 DiffStega 放置在本仓库同级或仓库根目录下的 `DiffStega/`，模型权重按 DiffStega 原 README 要求放入 `DiffStega/pretrained_models/`。这些第三方文件不会被 Git 跟踪。

## 环境准备

实验脚本主要面向 Windows + PowerShell + Conda 环境，原实验环境为 CUDA 12.x 与 Python 3.11。

```powershell
cd D:\thesis\release\thesis-steganalysis
.\setup_diffstega_env.ps1
```

如果只运行 CPU 友好的分析脚本，可在已有 Python 环境中安装分析依赖：

```powershell
python -m pip install -r requirements-analysis.txt
```

## 复现实验

生成传统 LSB 对照与基础统计分析：

```powershell
.\run_analysis.ps1
```

运行低显存 DiffStega 示例：

```powershell
.\run_diffstega_low_vram.ps1
```

运行高质量结果分析与参数汇总：

```powershell
.\run_hq_analysis.ps1
.\run_hq_calibration.ps1
.\run_hq_core.ps1
.\run_hq_ext.ps1
```

运行轻量隐写分析统计：

```powershell
python tools\lightweight_steganalysis.py
```

脚本会在 `experiments/` 下生成指标 CSV、对比图、残差图、直方图和参数敏感性结果。仓库内仅保留了少量样例结果，完整实验输出需要本地重新运行获得。

## 主要脚本

- `tools/lsb_baseline.py`：构造传统 LSB 隐写对照样例，并输出残差图和直方图。
- `tools/analyze_stego_results.py`：计算 PSNR、SSIM、MAE、RMSE，并生成 DiffStega/LSB 结果对比图。
- `tools/analyze_hq_results.py`：整理高质量实验输出，计算综合指标与参数敏感性。
- `tools/lightweight_steganalysis.py`：提取 LSB 比例、熵、卡方、残差、高频能量和边缘密度等轻量统计特征。
- `tools/combine_hq_analyses.py`：汇总多轮高质量实验指标。
- `tools/download_ip_adapter_models.py`：按 DiffStega 预期目录下载 IP-Adapter 依赖权重，权重不进入 Git 仓库。

## 开源范围

本仓库开源范围仅包括本人编写或整理的毕业设计配套脚本、说明材料和必要结果样例。第三方项目 DiffStega、IP-Adapter、预训练模型权重、虚拟环境和缓存文件均不属于本仓库开源内容。

## License

本仓库自研代码和整理文档采用 MIT License。第三方依赖项目及模型权重遵循其各自许可证和使用条款。
