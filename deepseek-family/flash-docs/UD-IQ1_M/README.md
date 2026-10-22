---
base_model: unsloth/Qwen3.8-Flash-Next-GGUF
base_model_relation: quantized
license: other
license_name: qwen-community-1.0
license_link: LICENSE
library_name: gguf
pipeline_tag: text-generation
language:
- en
- zh
tags:
- gguf
- qwen4exp
- qwen3.8-flash-next
- unsloth
- sakura
- cp2
---
# Sakura Qwen3.8 Flash-Next Compact · Unsloth UD-IQ1_M · 512E · CP2

Community repack of **Unsloth UD-IQ1_M**, retaining all **512 routed experts**. Shards 1 and 3 are unchanged. Shard 2 preserves its other weights and replaces only `per_layer_token_embd.weight` with the existing Sakura CP2 lookup data.

**This exact UD-IQ1_M + CP2 package has not been loaded for inference or tested for generation, perplexity, quality, speed or hardware fit.** The integrity/structural checks below do not establish model quality or transfer another Sakura package's results.

## Original versus Sakura

| Component / comparison | Bytes | Decimal GB | GiB |
|---|---:|---:|---:|
| Original matching Unsloth three-shard set | 74,538,755,776 | 74.539 | 69.420 |
| Original IQ4_NL table payload | 28,800,138,240 | 28.800 | 26.822 |
| Existing CP2 table payload | 13,440,064,512 | 13.440 | 12.517 |
| **Sakura three main GGUFs** | **59,178,682,208** | **59.179** | **55.114** |
| **Net saving against matching Unsloth** | **15,360,073,568** | **15.360** | **14.305** |

Raw table-payload saving is 15,360,073,728 bytes. Rebuilt GGUF metadata adds 160 bytes, giving the net saving shown above. Runtime, starter and documentation are additional. Disk size is not memory consumption or proof that a package fits your GPU/UMA.

| GGUF shard | Original bytes | Sakura bytes | Treatment |
|---|---:|---:|---|
| 1 | 10,946,624 | 10,946,624 | Copied unchanged |
| 2 | 49,988,981,792 | 34,628,908,224 | Table replaced; other weights retained |
| 3 | 24,538,827,360 | 24,538,827,360 | Copied unchanged |

## Download and start on Windows

```text
hf download webmp3/Sakura-Qwen3.8-Flash-Next-Compact-Unsloth-UD-IQ1_M-512E-CP2-GGUF --local-dir Sakura-UD-IQ1_M-CP2
```

Keep all three numbered GGUFs, `START.cmd` and the complete `runtime` directory together. Start `START.cmd`, then open **http://127.0.0.1:18122**. The OpenAI-compatible endpoint is `/v1/chat/completions`.

Use the supplied Windows x64 Vulkan CP2 runtime. This custom table needs its matching decoder; arbitrary stock llama.cpp, LM Studio or unrelated forks are not qualified here. The runtime was used with the earlier Sakura K512 package, but **this exact Unsloth weight combination has not been loaded**. No tested 64-GB-Strix-Halo fit, peak memory, long-context or speed result is claimed for this variant. Existing model/runtime/starter filenames remain unchanged.

## What was verified

- Shards 1 and 3 and the shipped runtime matched their pinned HF source sizes and full-file LFS SHA-256 identities.
- Rebuilt shard 2's pinned header, tensor names, shapes, offsets and CP2 metadata were checked. Bounded table and non-table samples matched the donor/source.
- The original IQ4_NL input had a complete streaming SHA-256 check for UD-IQ1_S. Other source variants were compared using exact Xet interior content references and boundary bytes; these are not separately claimed full streaming hashes.
- The input IQ4_NL payload hash and output CP2 payload hash are recorded separately in [PROVENANCE.json](PROVENANCE.json). CP2 is lossy; the two payloads are not byte-identical.
- The 2026-10-22 review did **not** independently download and rehash the entire rebuilt shard. Model identities in [SHA256SUMS](SHA256SUMS) use HF's full-file LFS metadata.
- No new encoder, training, expert pruning or runtime port was performed for this repack. No full inference test has been performed.

Shard 2 contains the table **and other weights**. It is not a standalone reusable table file. Shard 1 contains metadata/tokenizer data without tensors; shard 3 holds the remaining weights.

## Provenance and license

Original model: [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next). Direct backbone: [unsloth/Qwen3.8-Flash-Next-GGUF](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF), revision `766911a6b7369840a91dbcd95f9f997acaab6cd6`. Existing CP2 data and runtime: [Sakura ISTA Q2_0 512E CP2](https://huggingface.co/webmp3/Sakura-Qwen3.8-Flash-Next-Compact-ISTA-Q2_0-512E-CP2-GGUF), revision `9b8fef370b812b3fd33787869d553793517245cb`.

The backbone recipe belongs to Unsloth; Qwen belongs to Qwen. Sakura supplies the lookup-table representation and repack, without claiming retraining, upstream authorship or endorsement. Model weights retain **Qwen Community License 1.0**, included in `LICENSE` / `LICENSE-QWEN`. Runtime software has its own MIT/third-party notices; those do not relicense the weights.

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

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

</details>
