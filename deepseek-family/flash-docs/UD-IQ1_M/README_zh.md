# Sakura Qwen3.8 Flash-Next · Unsloth UD-IQ1_M · 512E · CP2

本版本主体直接来自 Unsloth `UD-IQ1_M`，保留全部 512 个路由专家。第 1、3 分片逐字节不变；第 2 分片保留其他权重，仅将 n-gram/PLE 表替换为已有 Sakura CP2 数据。

| 内容 | 十进制 GB |
|---|---:|
| 对应 Unsloth 原始三分片 | 74.539 |
| 原始 IQ4_NL 表数据区 | 28.800 |
| CP2 表数据区 | 13.440 |
| **本版本三个主分片** | **59.179** |
| **净减少** | **15.360** |

全部文件合计 59,178,682,208 字节，即 55.114 GiB；不含运行时和小型说明文件。文件大小不等于显存或内存用量。**本权重组合未进行完整推理、生成、困惑度、速度或硬件适配测试。** 其他 Sakura 模型的分数不可移用。

模型主体来源：`unsloth/Qwen3.8-Flash-Next-GGUF`，版本 `766911a6b7369840a91dbcd95f9f997acaab6cd6`。CP2 数据和对应 Windows x64 Vulkan 运行时来自 [Sakura ISTA Q2_0 512E CP2](https://huggingface.co/webmp3/Sakura-Qwen3.8-Flash-Next-Compact-ISTA-Q2_0-512E-CP2-GGUF)，版本 `9b8fef370b812b3fd33787869d553793517245cb`。保留 Qwen Community License 1.0 及运行时独立许可。

下载完整仓库，将三个编号 GGUF、`START.cmd` 及完整 `runtime` 文件夹保持在一起，运行 `START.cmd`。CP2 是自定义查找表格式，需要随附运行时。这个 Unsloth 版本本身没有在 64 GB Strix Halo 上完成加载或运行验证。

已核对原始分片 1/3 和运行时的 HF 文件 SHA-256；重建分片 2 的表头、形状、偏移及少量表内/表外字节经过检查。2026-10-22 的复核没有独立下载并重哈希完整重建分片。输入 IQ4_NL 与输出 CP2 的哈希在 `PROVENANCE.json` 中分开记录。
