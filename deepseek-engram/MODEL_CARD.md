---
license: mit
base_model: peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF
base_model_relation: quantized
pipeline_tag: text-generation
tags:
  - gguf
  - deepseek
  - mixture-of-experts
  - engram
  - q3_k
  - project-maya
---

# Sakura DeepSeek V4.1 Flash 1017 — Engram Q3_K

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

## Sakura DeepSeek V4.1 Flash 1017 — Engram Q3_K

**在保留 Maya-S 主干的同时缩小 Engram 表：总大小从 339.48 GB 降至 262.68 GB。** 两张 N-gram/Engram 表由 **Q6_K 重新量化为 Q3_K**。四个模型主干分片直接从 Maya-S 复制，内容保持不变。

| 结果 | 数值 |
| --- | ---: |
| 完整主模型 GGUF 文件集 | **262.676 GB / 244.636 GiB** |
| 相比 Maya-S 减少 | **76.802 GB / 22.62%** |
| Engram 表有效载荷 | **从 161.285 GB 降至 84.483 GB** |
| 表有效载荷缩减比例 | **47.62%** |
| 完整云端构建及发布耗时 | **1 小时 27 分 29 秒** |

**未进行完整推理测试。**

### 来源与准确的量化输入

| 阶段 | 模型 / 仓库 | 作用 |
| --- | --- | --- |
| 原始模型 | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | DeepSeek 检查点与模型架构 |
| 本次构建的直接输入 | [peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF) 的 **Maya-S** 目录 | 已量化的主干与两张 Q6_K Engram 表 |
| 本仓库 | **webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF** | 保持不变的 Maya-S 主干，以及新编码的 Q3_K 表 |

表量化的直接输入是 **Maya-S 的第 5、6 分片**，固定使用版本 `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`。每一行 Q6_K 数据先反量化为 Float32，再由 ggml 的 Q3_K 量化器编码。因此，本次处理属于**对现有 Q6_K 表的再次量化**；Sakura 构建并未直接从 DeepSeek 原始 FP8 权重重新生成这些表。

Maya-S 的前四个分片在服务端复制。它们的文件大小与 LFS SHA256 均与固定版本的源文件一致。没有裁剪专家，也没有重新量化主干权重。

### DeepSeek 原版、Maya-S 与 Sakura 的对比

| 项目 | DeepSeek 原版 | peasantsmith 的 Maya-S | Sakura Engram Q3_K |
| --- | --- | --- | --- |
| 文件格式 | Safetensors | GGUF | GGUF |
| 专家权重 | 原始配置指定 FP4 | IQ2/IQ3 混合格式 | 沿用 Maya-S，保持不变 |
| Dense / Attention 权重 | FP8 及其他原始类型 | 主要为 Q8_0，同时保留其他类型 | 沿用 Maya-S，保持不变 |
| Engram 表 | FP8 | Q6_K | **Q3_K** |
| Engram 总行数 | 768,022,850 | 768,022,850 | **768,022,850** |
| 大型 Engram 表 | 参考版本 | 由 peasantsmith 量化 | **仅对这两张表重新编码** |
| 运行时 | DeepSeek 参考实现 / 兼容框架 | Project Maya | **需要包含 Q3_K Engram 补丁的 Project Maya** |

#### 文件大小与对比范围

| 文件集 / 组成部分 | 字节 | GB | GiB |
| --- | ---: | ---: | ---: |
| 官方检查点文件集：全部 48 个 Safetensors 文件之和 | 510,296,708,312 | 510.297 | 475.251 |
| Maya-S：六个主模型 GGUF 文件 | 339,477,953,988 | 339.478 | 316.163 |
| **Sakura：六个主模型 GGUF 文件** | **262,675,668,988** | **262.676** | **244.636** |
| Maya-S / Sakura 共用的原样主干：分片 1–4 | 178,193,155,104 | 178.193 | 165.955 |
| Maya-S 的 Q6_K 表有效载荷 | 161,284,798,500 | 161.285 | 150.208 |
| **Sakura 的 Q3_K 表有效载荷** | **84,482,513,500** | **84.483** | **78.680** |

**GB = 10⁹ 字节；GiB = 2³⁰ 字节。** 两张表的文件头合计另占 384 字节。小型 README、补丁、许可证与清单文件不计入 GGUF 总大小。

主模型范围相同、可以直接对比的是 **Maya-S 与 Sakura**。原版的 510.297 GB 是其完整的 48 文件 Safetensors 发布包；本页不据此声称经过范围校正的主模型压缩比例。Sakura 提供六分片主模型 GGUF 文件集，不附带额外的视觉 / DSpark 文件。磁盘文件大小不等于 RAM / VRAM 需求。

#### 保留了哪些 Maya-S 量化格式？

| 张量组 | 保留的 Maya-S 类型 |
| --- | --- |
| Routed Experts 的 Gate / Up | IQ2_XXS；前后各四层使用 IQ2_S |
| Routed Experts 的 Down | IQ3_XXS；前后各四层使用 IQ3_S |
| Attention、Shared Experts、Embeddings、Output、Engram Value Projection | Q8_0 |
| Router、Norms、Hyper-Connection Mixing、Attention Sinks | F32 |
| 较小的 Indexer 投影 | BF16 |
| 大型 Engram Embedding 表 | **Q6_K → Q3_K；唯一重新量化的张量组** |

本仓库名称中的 **Q3_K 指的是 Engram 表**。模型主干保留 Maya-S 原有的混合量化格式。

### 架构与表布局

已核对的原始配置包含 40 个文本层、5,120 的隐藏维度、每层 384 个 Routed Experts、每个 Token 选择 6 个专家，以及一个 Shared Expert。Engram 表对应 GGUF 层编号 1 和 14。配置支持最长为 4 的 N-gram，每行表数据包含 256 个值。

| 表 | 行数 | 每行值数 | Q3_K 有效载荷 |
| --- | ---: | ---: | ---: |
| `blk.1.engram_embd.weight` | 384,006,168 | 256 | 42,240,678,480 字节 |
| `blk.14.engram_embd.weight` | 384,016,682 | 256 | 42,241,835,020 字节 |
| **合计** | **768,022,850** | — | **84,482,513,500 字节** |

| 格式细节 | Maya-S 输入 | Sakura 输出 |
| --- | ---: | ---: |
| GGML 类型 | Q6_K / 14 | Q3_K / 11 |
| 每个块 / 每行的值数 | 256 | 256 |
| 每行字节数，包含块缩放参数 | 210 | 110 |
| 每个值的实际位数，包含块缩放参数 | 6.5625 | 3.4375 |

张量名称、维度、行数与表寻址方式保持不变。GGUF 张量类型正确设为 **11 / Q3_K**；新数据没有被标记为 Q6_K。

原始配置允许最多 1,048,576 个上下文位置。这是架构配置值；本次 Sakura 构建没有进行上下文长度或内存占用基准测试。

### 文件与校验值

六个 GGUF 文件均位于 [Maya-S/](tree/main/Maya-S)。共同文件名前缀为 `DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-`。

| 文件名后缀 | 内容 | 字节大小 |
| --- | --- | ---: |
| `00001-of-00006.gguf` | 保持不变的主干 | 47,887,697,312 |
| `00002-of-00006.gguf` | 保持不变的主干 | 47,669,578,400 |
| `00003-of-00006.gguf` | 保持不变的主干 | 47,103,347,360 |
| `00004-of-00006.gguf` | 保持不变的主干 | 35,532,532,032 |
| `00005-of-00006.gguf` | 第 1 层 Engram 表，**Q3_K** | 42,240,678,672 |
| `00006-of-00006.gguf` | 第 14 层 Engram 表，**Q3_K** | 42,241,835,212 |

保留原始分片名称是为了维持分片识别。虽然文件名中仍含有 `IQ2_XXS`，但第 5、6 分片中的表实际为 **Q3_K**，以已验证的 GGUF 文件头为准。

[构建清单](resolve/main/build-manifest.json)包含六个文件的大小与 SHA256、源版本、补丁哈希以及两张表的完整构建报告。单独的报告见 [build/shard5.json](resolve/main/build/shard5.json) 和 [build/shard6.json](resolve/main/build/shard6.json)。

### 实际云端构建

| 步骤 / 测量项目 | 结果 |
| --- | --- |
| 执行环境 | 公开仓库的标准 `ubuntu-24.04` CPU Runner；两个表任务并行 |
| 完整工作流 | **1 小时 27 分 29 秒** |
| 第 5 分片：哈希、编码与上传验证 | 5,179.107 秒，约 86 分 19 秒 |
| 第 6 分片：哈希、编码与上传验证 | 4,780.244 秒，约 79 分 40 秒 |
| Runner 读取的 Q6_K 源数据 | 322,569,597,000 字节，恰好两次有效载荷遍历 |
| 新 Q3_K 表 | 84,482,513,500 字节有效载荷，加 384 字节文件头 |
| 主干 | 四个文件在服务端复制，源 LFS SHA256 保持一致 |
| 最终验证 | 六个文件的大小与远端 LFS SHA256 均与清单核对 |
| 资源 | CPU；未使用 GPU、付费 Runner 或推理 API |

表文件通过确定性、支持随机定位的量化数据流生成，RAM 中只保留有界数据块。哈希与上传阶段分别读取、编码同一份源数据。Runner 磁盘上没有生成完整的约 42 GB 输出表文件。完整构建不依赖用户电脑。

### 运行时与使用方式

需要给 [Project Maya](https://github.com/mw00/project-maya) 应用随附的 [Maya Q3_K Engram 补丁](resolve/main/runtime/maya-q3k.patch)。补丁已针对版本 `451f9cb6a21ea65673bdde2e57b4a670ae2b8859` 检查。

该补丁在 Engram 读取器及相关解码器中明确增加 Q3_K 支持。打包器或其他运行时具备通用 Q3_K 支持，并不代表其支持这一特定的表读取路径。

补丁以源代码提供，目标是上述 Maya 版本；本仓库不提供预编译的 Sakura Windows / HIP 启动器。已修改的 CUDA 编译单元完成编译，GPU 一致性测试程序完成链接。尚未验证 GPU 执行、完整 Maya 可执行程序的链接，以及 HIP / Windows 运行。视觉与 DSpark 功能可能需要另行取得上游组件。

### 验证与质量比较

| 本次构建执行的检查 | 结果 |
| --- | --- |
| 真实数据 CPU 小规模测试 | 从两张表的开头、中间与末尾抽取，共 98,304 行 Q6_K 数据 |
| 重复量化样本块 | 每个样本编码三次，Q3_K SHA256 均一致 |
| Q3_K CPU 解码器与 ggml 对照 | 在 192 行真实量化数据、4,096 个随机块以及 63,488 个有限 FP16 缩放值上逐位一致 |
| Maya 读取器 / 缓存 | 检查了 64 位偏移、Token 槽位、重复项、缓存淘汰与短读取 |
| GGUF 流式读取 / HF 兼容性 | 检查了随机定位、块边界、重复哈希与分段上传重组 |
| 完整输出文件 | 验证了大小与远端 LFS SHA256 |
| 发布后的额外文件头检查 | 两个 192 字节文件头均符合预期 Q3_K 布局 |

CPU 小规模测试中，六个样本块相对于**现有 Q6_K 输入**的 RRMSE 约为 **15.209%–15.233%**。该数值衡量的是表值的数值差异，不是与原始 FP8 表的比较，也不是困惑度、编程能力、回答质量或推理速度评测。

[固定源版本的 Maya-S 模型卡](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/b9e25f34b53806b24e5b18085de6ed5967ad9ed5/README.md)另外报告了相对于 DeepSeek 参考实现的以下测量，使用 10 段留出序列，每段 2,047 个 Token：

| peasantsmith 报告的上游测量 | 相同 Top-Token 比例 | KL 散度 |
| --- | ---: | ---: |
| 原始权重通过 Maya 引擎运行 | 96.4% | 0.047 |
| 使用 Q6_K 表的 Maya-S | 92.6% | 0.120 |
| **使用 Q3_K 表的 Sakura** | **未测量** | **未测量** |

前两项上游结果没有在本次工作中复测，也不作为 Sakura 的结果。它们对应源模型卡描述的 Token 对比方法，不是通用任务得分。本仓库不声称 Sakura 模型质量保持不变，也不声称每秒生成 Token 数有所增加。

### 可复现的来源

| 组成部分 | 固定版本 |
| --- | --- |
| 直接使用的 Maya-S 输入模型 | `b9e25f34b53806b24e5b18085de6ed5967ad9ed5` |
| 官方 DeepSeek 检查点、配置与大小清单 | `1bae0e1088993b9b82de08f59de5be5a34e42170` |
| 应用 Sakura 补丁前的 Maya 引擎 | `451f9cb6a21ea65673bdde2e57b4a670ae2b8859` |
| llama.cpp / ggml CPU 量化器 | `c7fc5094179bf8a9c73c18593db714f8da41a402` |
| 随附运行时补丁的 SHA256 | `e5e2c5d50633fcf1fb57478656e6bce4d7453d06ea43b2381c9da6fe395f0cfd` |

架构与原始格式来自[固定版本的 DeepSeek 配置](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/config.json)。原始发布包大小由该版本 48 个 Safetensors 文件的大小元数据求和得出；为取得这些数字，没有下载原始权重有效载荷。

### 许可证与致谢

模型与量化遵循原始模型及 Maya-S 发布的 **MIT** 许可证。随附许可证文件为 [LICENSE.DeepSeek](resolve/main/LICENSE.DeepSeek)、[LICENSE.Maya](resolve/main/LICENSE.Maya) 和 [LICENSE.llama.cpp](resolve/main/LICENSE.llama.cpp)。

基础模型：**DeepSeek-AI**。Maya-S 量化与表数据来源：**peasantsmith**。运行时：**Project Maya**。CPU 量化器：**ggml / llama.cpp**。Sakura 仅修改两张大型 Engram 表，并增加读取这些表所需的 Maya 解码支持。

</details>

**Maya-S with smaller Engram tables: 262.68 GB instead of 339.48 GB.** Both N-gram/Engram tables have been requantized from **Q6_K to Q3_K**. The four backbone files are copied unchanged from Maya-S.

| Result | Value |
| --- | ---: |
| Complete main-model GGUF set | **262.676 GB / 244.636 GiB** |
| Reduction versus Maya-S | **76.802 GB / 22.62%** |
| Engram table payload | **84.483 GB instead of 161.285 GB** |
| Table payload reduction | **47.62%** |
| Complete cloud build, including publication | **1 h 27 min 29 s** |

**No full inference test has been performed.**

## Provenance and exact quantization source

| Stage | Model / repository | Role |
| --- | --- | --- |
| Original model | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | DeepSeek checkpoint and architecture |
| Direct input to this build | [peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF), **Maya-S** folder | Previously quantized backbone and two Q6_K Engram tables |
| This repository | **webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF** | Unchanged Maya-S backbone with newly encoded Q3_K tables |

The direct inputs to table quantization were **Maya-S shards 5 and 6**, pinned to revision `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`. Each Q6_K row was dequantized to Float32 and then encoded with the ggml Q3_K quantizer. This is a **requantization of the existing Q6_K tables**. The Sakura build did not regenerate the tables from DeepSeek's original FP8 weights.

The first four Maya-S shards were copied server-side. Their sizes and LFS SHA256 values match the pinned source. No experts were removed, and no backbone weights were requantized.

## Comparison: original DeepSeek, Maya-S and Sakura

| Feature | Original DeepSeek | Maya-S by peasantsmith | Sakura Engram Q3_K |
| --- | --- | --- | --- |
| File format | Safetensors | GGUF | GGUF |
| Expert weights | FP4 according to the original configuration | Mixed IQ2/IQ3 formats | Unchanged from Maya-S |
| Dense/attention weights | FP8 and other original types | Primarily Q8_0, with other types retained | Unchanged from Maya-S |
| Engram tables | FP8 | Q6_K | **Q3_K** |
| Number of Engram rows | 768,022,850 | 768,022,850 | **768,022,850** |
| Large Engram tables | Reference | Quantized by peasantsmith | **Only these two tables are newly encoded** |
| Runtime | DeepSeek reference implementation / compatible frameworks | Project Maya | **Project Maya with the included Q3_K Engram patch** |

### File sizes and comparison scope

| Package / component | Bytes | GB | GiB |
| --- | ---: | ---: | ---: |
| Official checkpoint package, sum of all 48 Safetensors files | 510,296,708,312 | 510.297 | 475.251 |
| Maya-S, six main-model GGUF files | 339,477,953,988 | 339.478 | 316.163 |
| **Sakura, six main-model GGUF files** | **262,675,668,988** | **262.676** | **244.636** |
| Unchanged Maya-S/Sakura backbone, shards 1–4 | 178,193,155,104 | 178.193 | 165.955 |
| Maya-S table payload, Q6_K | 161,284,798,500 | 161.285 | 150.208 |
| **Sakura table payload, Q3_K** | **84,482,513,500** | **84.483** | **78.680** |

**GB = 10⁹ bytes; GiB = 2³⁰ bytes.** The two table headers add 384 bytes in total. Small README, patch, license and manifest files are excluded from the GGUF totals.

The direct comparison with identical main-model scope is **Maya-S versus Sakura**. The original's 510.297 GB is the entire published 48-file Safetensors package; no scope-adjusted main-model reduction is claimed against that figure. Sakura contains the six-part main-model GGUF set. Additional vision/DSpark files are not included here. File sizes are not RAM/VRAM requirements.

### Which Maya-S quantization is preserved?

| Tensor group | Retained Maya-S types |
| --- | --- |
| Routed experts, gate/up | IQ2_XXS; IQ2_S in the first/last four layers |
| Routed experts, down | IQ3_XXS; IQ3_S in the first/last four layers |
| Attention, shared experts, embeddings, output, Engram value projection | Q8_0 |
| Router, norms, hyper-connection mixing, attention sinks | F32 |
| Small indexer projections | BF16 |
| Large Engram embedding tables | **Q6_K → Q3_K; the only newly quantized tensor group** |

Thus, **Q3_K in this repository refers to the Engram tables**. The backbone retains Maya-S's mixed quantization.

## Architecture and table layout

The checked original configuration specifies 40 text layers, a hidden size of 5,120, 384 routed experts per layer, 6 selected experts per token and one shared expert. The Engram tables belong to GGUF layers 1 and 14. The configuration supports N-grams up to length 4 and uses 256 values per table row.

| Table | Rows | Values per row | Q3_K payload |
| --- | ---: | ---: | ---: |
| `blk.1.engram_embd.weight` | 384,006,168 | 256 | 42,240,678,480 bytes |
| `blk.14.engram_embd.weight` | 384,016,682 | 256 | 42,241,835,020 bytes |
| **Total** | **768,022,850** | — | **84,482,513,500 bytes** |

| Format detail | Maya-S input | Sakura output |
| --- | ---: | ---: |
| GGML type | Q6_K / 14 | Q3_K / 11 |
| Values per block / row | 256 | 256 |
| Bytes per row, including block scales | 210 | 110 |
| Effective bits per value, including block scales | 6.5625 | 3.4375 |

Tensor names, dimensions, row counts and table addressing are preserved. The GGUF tensor type is correctly set to **11 / Q3_K**; the new data is not labeled as Q6_K.

The original configuration allows up to 1,048,576 context positions. This is an architecture setting; no context-length or memory benchmark has been performed for this Sakura build.

## Files and checksums

All six GGUF files are in [Maya-S/](tree/main/Maya-S). Their common filename prefix is `DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-`.

| Filename suffix | Contents | Size in bytes |
| --- | --- | ---: |
| `00001-of-00006.gguf` | Unchanged backbone | 47,887,697,312 |
| `00002-of-00006.gguf` | Unchanged backbone | 47,669,578,400 |
| `00003-of-00006.gguf` | Unchanged backbone | 47,103,347,360 |
| `00004-of-00006.gguf` | Unchanged backbone | 35,532,532,032 |
| `00005-of-00006.gguf` | Engram, layer 1, **Q3_K** | 42,240,678,672 |
| `00006-of-00006.gguf` | Engram, layer 14, **Q3_K** | 42,241,835,212 |

The original shard names are retained for split identification. Although the filenames still contain `IQ2_XXS`, the tables in shards 5/6 are **Q3_K**, as recorded in their verified GGUF headers.

The [build manifest](resolve/main/build-manifest.json) contains all six file sizes and SHA256 values, the source revision, patch hash and complete build reports for both tables. Separate reports are available as [build/shard5.json](resolve/main/build/shard5.json) and [build/shard6.json](resolve/main/build/shard6.json).

## Actual cloud build

| Step / measurement | Result |
| --- | --- |
| Execution environment | Public standard `ubuntu-24.04` CPU runners; two table jobs in parallel |
| Complete workflow | **1 h 27 min 29 s** |
| Table 5, hashing/encoding and upload verification | 5,179.107 s / approximately 86 min 19 s |
| Table 6, hashing/encoding and upload verification | 4,780.244 s / approximately 79 min 40 s |
| Q6_K source data read on the runners | 322,569,597,000 bytes, exactly two payload passes |
| New Q3_K tables | 84,482,513,500 payload bytes plus 384 header bytes |
| Backbone | Four files copied server-side; source LFS SHA256 values preserved |
| Final verification | All six sizes and remote LFS SHA256 values checked against the manifest |
| Resources | CPU; no GPU, paid runners or inference API |

The tables were generated as a deterministic, seekable quantization stream using bounded RAM blocks. The same source data was read and encoded again for hashing and upload. No complete 42 GB output table was materialized on the runner's disk. The user's PC was not involved in the full build.

## Runtime and usage

The included [Maya Q3_K Engram patch](resolve/main/runtime/maya-q3k.patch) is required for [Project Maya](https://github.com/mw00/project-maya). It was checked against revision `451f9cb6a21ea65673bdde2e57b4a670ae2b8859`.

The patch explicitly adds Q3_K to the Engram reader and the associated decoders. Generic Q3_K support in a packer or another runtime does not establish support for this particular table path.

The patch is provided as source code. It targets the specified Maya revision; no prebuilt Sakura Windows/HIP launcher is included. The modified CUDA translation units were compiled and the GPU parity-test executable was linked. GPU execution, a full Maya executable link and HIP/Windows operation have not been demonstrated. Vision and DSpark may require the separate upstream components.

## Verification and quality comparison

| Check performed for this build | Result |
| --- | --- |
| CPU pilot on real data | 98,304 Q6_K rows from the beginning, middle and end of both tables |
| Repeated pilot-block quantization | Identical Q3_K SHA256 values across three encodings of each sample |
| Q3_K CPU decoder versus ggml | Bit-exact parity on 192 real quantized rows, 4,096 random blocks and 63,488 finite FP16 scales |
| Maya reader/cache | 64-bit offsets, token slots, duplicates, eviction and short reads checked |
| GGUF streaming / HF compatibility | Seeking/block boundaries, repeated hashing and multipart reconstruction checked |
| Complete output files | Sizes and remote LFS SHA256 values verified |
| Additional post-release header check | Both 192-byte headers match the expected Q3_K layout |

In the CPU pilot, the six sample blocks had RRMSE values of approximately **15.209%–15.233%** relative to the **existing Q6_K input**. This measures numerical differences in table values. It is not a comparison with the original FP8 tables, or a perplexity, coding, response-quality or inference-speed evaluation.

The [Maya-S model card at the source revision](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/b9e25f34b53806b24e5b18085de6ed5967ad9ed5/README.md) separately reports the following comparison against DeepSeek's reference, using 10 held-out sequences of 2,047 tokens each:

| Upstream measurement by peasantsmith | Same top token | KL divergence |
| --- | ---: | ---: |
| Original weights through Maya's engine | 96.4% | 0.047 |
| Maya-S with Q6_K tables | 92.6% | 0.120 |
| **Sakura with Q3_K tables** | **Not measured** | **Not measured** |

The two upstream results were not reproduced here and are not presented as Sakura results. They refer to the token-comparison method described by the source, rather than general task scores. No claim of unchanged model quality or additional tokens/s is made for Sakura.

## Reproducible sources

| Component | Pinned version |
| --- | --- |
| Direct Maya-S input model | `b9e25f34b53806b24e5b18085de6ed5967ad9ed5` |
| Official DeepSeek checkpoint, configuration and size inventory | `1bae0e1088993b9b82de08f59de5be5a34e42170` |
| Maya engine before the Sakura patch | `451f9cb6a21ea65673bdde2e57b4a670ae2b8859` |
| llama.cpp / ggml CPU quantizer | `c7fc5094179bf8a9c73c18593db714f8da41a402` |
| SHA256 of the included runtime patch | `e5e2c5d50633fcf1fb57478656e6bce4d7453d06ea43b2381c9da6fe395f0cfd` |

Architecture details and the original format come from the [pinned DeepSeek configuration](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/config.json). The original package size was calculated by summing metadata sizes for all 48 Safetensors files at that revision. No original weight payload was downloaded to obtain those figures.

## License and acknowledgments

Model and quantization: **MIT**, following the original and Maya-S releases. Included license texts are [LICENSE.DeepSeek](resolve/main/LICENSE.DeepSeek), [LICENSE.Maya](resolve/main/LICENSE.Maya) and [LICENSE.llama.cpp](resolve/main/LICENSE.llama.cpp).

Base model: **DeepSeek-AI**. Maya-S quantization and table source: **peasantsmith**. Runtime: **Project Maya**. CPU quantizer: **ggml / llama.cpp**. Sakura changes only the two large Engram tables and adds the Maya decoder support required to read them.
