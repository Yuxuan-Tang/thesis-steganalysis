# 轻量隐写分析特征对比解释

本实验不接入深度隐写分析器，而是使用低位统计和残差特征对 LSB 修改式隐写与 DiffStega 生成式载密图像进行机制层面的轻量对比。

LSB 对照中，cover 与 stego 在视觉上非常接近，但最低有效位统计和残差特征仍可被单独计算。
本实验中 LSB cover 的 LSB entropy 均值为 0.983239，LSB stego 的 LSB entropy 均值为 0.920857；
LSB cover 的 chi-square pair 均值为 2355.028662，LSB stego 的 chi-square pair 均值为 2397.059669。

DiffStega 载密图像不是在已有 cover 上进行 LSB 嵌入，因此本实验不把传统 LSB 检测结果解释为完整安全证明。
DiffStega stego 组的 LSB entropy 均值为 0.999551，chi-square pair 均值为 66.064019，可作为与 LSB 修改式隐写的低位统计对照。
论文中应表述为：DiffStega 载密生成图像未表现出传统 LSB 型最低有效位嵌入的直接修改机制，但其安全性仍需要深度隐写分析器和生成图像检测器进一步验证。