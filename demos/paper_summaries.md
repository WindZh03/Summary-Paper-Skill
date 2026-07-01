---
title: Paper Summaries
paper_count: 2
generated_by: Summary-Papers
---

# Paper Summaries

## Overview
- Total papers: 2

## Papers

### 1. FreqPhys: Repurposing Implicit Physiological Frequency Prior for Robust Remote Photoplethysmography

- 作者: Wei Qian, Dan Guo, Jinxing Zhou, Bochao Zou, Zitong Yu, Meng Wang
- 年份: 2026
- 发表期刊/会议: arXiv preprint (arXiv:2604.00534)
- 关键词: Remote photoplethysmography; Physiological frequency priors; Conditional diffusion
- GitHub: 未找到
- PDF: xxx
- Zotero: 未提供


#### 研究现状
现有 rPPG 方法主要依赖时域建模，虽有一些工作引入频域信息（频谱损失、傅里叶模块、频域增强），但仅作为辅助监督或特征增强，未显式利用生理频率先验来指导去噪过程。

#### Motivation
时域中生理信号与噪声高度纠缠，运动伪影和光照波动极易淹没微弱的皮肤颜色变化信号，导致现有方法在复杂场景下性能严重退化。

#### Insight
rPPG 信号由准周期性心搏驱动，在频域呈现强结构先验：生理频带约束（[0.66, 3.0] Hz）和主峰特性；利用这些先验可同时抑制带外干扰和带内残余噪声。

#### 核心贡献
提出 FreqPhys，一个频率感知的扩散框架，显式将生理频率先验融入在线去噪过程：(1) 生理带通滤波器去除带外噪声；(2) 生理频谱调制增强真实心搏谐波；(3) 自适应频谱选择抑制带内残留噪声；并通过跨域表示学习融合频域先验与时域特征。

#### 方法
首先构建多尺度时空图（MSTmap）作为输入。通过生理带通滤波器（PBF）保留 [0.66, 3.0] Hz 成分，利用可学习的复数权重对频谱进行调制（PSM），再通过数据驱动的能量阈值自适应选择优势频率成分（ASS）。跨域表示学习模块通过交替的交叉注意力机制融合频域去噪后的表示与时域中间特征。最后采用频率条件扩散模型（DDPM）逐步重构高保真 rPPG 信号。训练和推理时每个扩散步骤均应用三级渐进式频域去噪。

#### 实验结论
在六个公开基准数据集（含稳定和运动场景）上取得显著优于现有方法的结果，尤其在挑战性运动条件下提升明显。频率引导的扩散框架在鲁棒性和泛化性上均超越纯时域扩散方法和传统频域辅助方法。

#### 局限性
扩散模型推理速度较慢，计算开销较大；自适应频谱选择中的硬掩码通过直通估计器训练，可能存在梯度偏差；方法依赖心率落在 [0.66, 3.0] Hz 范围的假设，极端心率情况可能受影响。

#### 其它
源代码将公开发布。首次将生理频率先验作为内部结构约束直接融入扩散模型的在线去噪过程，而非作为外部辅助线索。在频域卷积定理的数学保证下实现内容自适应的感受野。

### 2. Passive heart-rate monitoring during smartphone use in everyday life

- 作者: Shun Liao, Paolo Di Achille, Jiang Wu, Silviu Borac, Jonathan Wang, Xin Liu, Eric S. Teasley, Lawrence Cai, Yuzhe Yang, Yun Liu, Daniel McDuff, Hao-Wei Su, Brent Winslow, Anupam Pathak, Mark Malhotra, Shwetak Patel, James A. Taylor, Jameson K. Rogers, Ming-Zher Poh
- 年份: 2026
- 发表期刊/会议: Nature
- 关键词: Remote photoplethysmography; Passive heart rate monitoring; Resting heart rate; Deep learning; Skin tone fairness
- GitHub: 未找到
- PDF: xxx
- Zotero: 未提供


#### 研究现状
现有 rPPG 研究样本量小、局限于受控环境、真实世界泛化能力差，且深肤色人群准确率显著下降。可穿戴设备普及率有限，难以大规模实现纵向静息心率监测。

#### Motivation
智能手机已普及（全球 69% 拥有率），每日使用约 144 次，可作为被动心率监测的理想载体，但缺乏大规模多样化验证，尤其缺乏对深肤色人群的公平性评估。

#### Insight
将心率估计重构为离散化心率范围（40-180 bpm）上的多分类问题，使模型能通过概率分布表达不确定性，配合置信度门控有效过滤噪声估计。

#### 核心贡献
迄今最大规模的 rPPG 验证研究（192,353 训练视频 + 162,546 验证视频，485+211 参与者）；在所有肤色组上 MAPE < 10% 满足 FDA/ANSI 标准；实现被动日常 RHR 追踪（MAE < 5 bpm vs 可穿戴设备）；公开大规模标注数据集和预训练模型。

#### 方法
系统包含两大模块：(1) 端到端 HR 估计——8 秒面部视频片段经视频稳定、人脸裁剪、帧差预处理后，输入时序移位卷积神经网络（TSCNN）集成模型，将 HR 估计建模为 40-180 bpm 离散心率范围上的多分类问题，输出概率分布和置信度分数；(2) 每日 RHR 计算——利用置信度门控过滤无效测量，通过卡尔曼滤波器聚合全天有效 HR 测量值。系统在屏幕解锁时自动触发前置摄像头被动采集。

#### 实验结论
实验室环境：参与者水平 MAPE 5.65%，三组肤色 MAPE 分别为 3.81%/4.43%/8.93%，全部显著低于 10% 目标。自然生活环境：视频水平 MAPE 4.83%，参与者水平 MAPE 6.09%，三组肤色 MAPE 均 < 10%，肤色组间差异满足预设非劣效标准（< 5 个百分点）。Bland-Altman 分析显示极小偏倚。PHRM 在所有肤色组上大幅优于 15 个对比模型。

#### 局限性
自由生活环境下视频级测量成功率从实验室的 77.7% 降至 43.1%，深肤色组（MST 8-10）仅 25%。需要屏幕解锁事件触发采集，无法覆盖非手机使用时段。部分参与者因面部标志点检测失败导致无有效测量。

#### 其它
数据覆盖 26 种手机型号，光照范围覆盖日常全动态范围（从暗光到室外）。使用 Monk Skin Tone（MST）量表实现更具包容性的肤色表示。遵循 FDA 关于临床试验多样性的人群采样建议。发布了预训练模型和大规模标注视频数据集。
