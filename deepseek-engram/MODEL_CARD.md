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
