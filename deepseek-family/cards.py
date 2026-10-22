"""English comparison cards, collapsed Chinese translation, family overview."""
def gb(n):return f'{n/1e9:.3f}'
def comparison(p):
 rows='\n'.join(f"| [{v['variant']}](https://huggingface.co/{v['repo']}) | {gb(v['original_bytes'])} | {gb(sum(f['size'] for f in v['backbone']))} | **{gb(v['main_bytes'])}** | {gb(v['original_bytes']-v['main_bytes'])} |" for v in sorted(p['variants'],key=lambda x:x['main_bytes']))
 return '| Sakura package | Matching upstream GB | Unchanged backbone GB | Sakura main files GB | Saving GB |\n|---|---:|---:|---:|---:|\n'+rows

def model_card(p,v,m,complete_family=False):
 body=sum(f['size'] for f in v['backbone']);tab=sum(f['size'] for f in v['tables']);saved=v['original_bytes']-v['main_bytes'];q=v['variant'];maya=v['kind']=='maya';count=len(v['backbone'])+len(v['tables'])
 files='\n'.join(f"| `{f['path']}` | {f['size']:,} | `{f['sha256']}` |" for f in m['files'])
 if maya:
  runtime=f"Use [Project Maya](https://github.com/mw00/project-maya/tree/{v['runtime_revision']}) at `{v['runtime_revision']}` with the included [Q3_K source patch](runtime/maya-v1.1.22-q3.patch). Maya-XS needs this revision's IQ1_S/IQ1_M backbone support. Apply the patch to that exact revision and build using Maya's CUDA or HIP instructions. The scalar Q3 decoder was checked against GGML. CUDA translation units and the isolated GPU test were compiled and linked without GPU execution. HIP compilation, Windows operation and full-model loading remain untested."
 else:
  runtime=f"Use a runtime supporting this Unsloth DeepSeek-4.1 layout: the inspected [danielhanchen/llama.cpp source](https://github.com/danielhanchen/llama.cpp/tree/{v['runtime_revision']}) at `{v['runtime_revision']}` ([PR #30817](https://github.com/ggml-org/llama.cpp/pull/30817)). Its native host-gather Q3_K path was checked on 192 real rows, both layer boundaries, reverse gathers and 64-bit offsets. See the [Unsloth guide](https://unsloth.ai/docs/models/deepseek-v4.1-flash). This does not qualify arbitrary stock llama.cpp, LM Studio or Maya versions."
 scope='two separate layer tables' if maya else 'one combined table, layer 1 followed by layer 14'
 original_maya=v['group']=='existing-maya'
 payload_action='Original build: Q6_K to Q3_K; this documentation update changes no weights' if original_maya else 'Existing Sakura Q3_K data reused without another quantization pass'
 transformation='The original Maya-S release quantized its Q6_K table input to Q3_K on a CPU. This model-card/runtime-source update does not rebuild or change its model files.' if original_maya else 'This repack does not requantize the upstream IQ4_NL, Q5_K, Q6_K or MXFP8 table. It reuses the existing Q3 payload and adjusts only the GGUF table header where required.'
 family='## Compare the Sakura DeepSeek releases\n\n[Open the complete family overview](https://huggingface.co/'+p['overview_repo']+').\n\n'+comparison(p)+'\n\nThese compare disk sizes and source recipes, not measured answer quality.\n\n' if complete_family else ''
 return f'''---
license: mit
base_model: {v['source_repo']}
base_model_relation: quantized
pipeline_tag: text-generation
language:
- en
- zh
tags:
- gguf
- deepseek
- sakura
- engram
- q3_k
- mixture-of-experts
---
# Sakura DeepSeek-V4.1-Flash-1017 · {q} · Engram Q3_K

**The original {q} backbone is unchanged. Only the separate Engram lookup-table files are replaced with Q3_K. All experts and all lookup rows are retained.**

**No full inference test has been performed.** The checks cover integrity, format, addressing and isolated decoder paths. No generation-quality, perplexity, speed or hardware-fit score is claimed for this exact package.

## Original versus Sakura

| Component | Bytes | Decimal GB |
|---|---:|---:|
| Matching upstream main GGUF set | {v['original_bytes']:,} | {gb(v['original_bytes'])} |
| Unchanged upstream backbone | {body:,} | {gb(body)} |
| Upstream Engram files | {v['original_bytes']-body:,} | {gb(v['original_bytes']-body)} |
| Replacement Q3_K Engram files | {tab:,} | {gb(tab)} |
| **Sakura main GGUF set** | **{v['main_bytes']:,}** | **{gb(v['main_bytes'])}** |
| **Saved versus this upstream variant** | **{saved:,}** | **{gb(saved)} ({100*saved/v['original_bytes']:.2f}%)** |

Main files: **{v['main_bytes']/1024**3:.3f} GiB**. Optional DSpark/drafter, vision, imatrix, runtime and documentation are outside this main-model total. File size is not RAM/VRAM consumption or proof that the package fits a particular machine.

## What changed and what stayed identical

| Part | Treatment |
|---|---|
| {len(v['backbone'])} backbone shards, including tokenizer/model metadata | Copied server-side; source sizes and full HF LFS SHA-256 identities retained |
| Routed experts | No pruning, retraining or requantization by Sakura |
| Engram lookup payload | {payload_action} |
| Table layout | {scope}; correct split index/count and source tensor-count contract |
| Actual format | GGML type 11 / Q3_K, 110 bytes per 256-value row |

The `{q}` label describes the upstream backbone recipe. **Q3_K describes the Engram tables, not the entire model.**

## Provenance

- Original checkpoint: [{p['original_repo']}](https://huggingface.co/{p['original_repo']}), revision `{p['original_revision']}`.
- Direct backbone: [{v['source_repo']}](https://huggingface.co/{v['source_repo']}/tree/{v['source_revision']}), revision `{v['source_revision']}`.
- Q3 payload: [Sakura Maya-S Engram Q3_K](https://huggingface.co/{p['split_sources']['repo']}), frozen input revision `{p['split_sources']['revision']}`. It was quantized from peasantsmith's Maya-S Q6_K tables at `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`, using GGML `c7fc5094179bf8a9c73c18593db714f8da41a402`.
- {transformation}

The official safetensors checkpoint is about 510.297 GB as a broader package; original Maya-S is 339.478 GB. These are context, not scope-matched quality or memory baselines. The matching-upstream row above is this release's reduction baseline.

## Table geometry and addressing

| Property | Value |
|---|---|
| Engram layers | 1 and 14 |
| Layer row counts | 384,006,168 / 384,016,682 |
| Total rows | 768,022,850 |
| Values per row | 256 |
| Total Q3 payload | 84,482,513,500 bytes |
| Storage | {scope} |
| Combined second-layer starting row, where applicable | 384,006,168 |

Tokenizer-derived token mapping, hash constants, bucket sizes and addressing metadata were compared against the relevant source layout. A 192-row Q6 sample matched Maya and Unsloth before the original table reuse. Maya-XS additionally matched 96 Q6 sample rows and the complete token-map hash. Samples alone do not prove complete original Q6 payload identity.

## Download and load

```text
hf download {v['repo']} --local-dir Sakura-{q}-Engram-Q3_K
```

Keep all {count} numbered GGUF files together. Load `{v['backbone'][0]['path']}` with the matching runtime.

{runtime}

## What was verified

| Check | Result and scope |
|---|---|
| Backbone identity | Every copied file's size and LFS SHA-256 matched the pinned source |
| Table stream | Header-only repacks verify complete existing Q3 input hashes and independent Python/native output hashes; see the build record |
| Published table layout | Exact headers, shapes, real types, offsets and split metadata checked |
| Published real-row samples | 192 Q3 rows across both layers, including middle/final rows, compared with frozen fixtures |
| Decoder and addressing | Isolated CPU checks; see [compatibility record](compatibility-check.json) |
| Full inference, generation quality, perplexity and speed | **Not tested for this exact package** |
| GPU execution / Windows / AMD qualification | **Not performed** |

Upstream benchmarks and another Sakura variant's results are not measurements of this package. Row reconstruction error is not model quality. Build evidence and exact file identities: [build-manifest.json](build-manifest.json).

{family}## Exact main files

| File | Bytes | SHA-256 |
|---|---:|---|
{files}

## Credits and license

DeepSeek-AI: original model and Engram. Unsloth / peasantsmith / Project Maya: the credited upstream recipes and runtimes. GGML / llama.cpp: Q3_K format, reference quantizer and decoder. Sakura: table compression, format adaptation, integrity checks and release assembly. No upstream endorsement or authorship of its backbone is claimed.

MIT model/source notices are retained in the included license files. Builds use free public standard CPU runners, no paid runner/GPU or inference API. Public HF storage is best-effort; no quota-neutral deduplication is promised.

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

## 模型、来源与大小比较

本版本保留 **{q}** 原始模型主体，所有专家和查找行均保留；仅将独立的 Engram 表文件替换为 Q3_K。Q3_K 只描述查找表，不表示整个模型都是 3 位。

| 内容 | 十进制 GB |
|---|---:|
| 对应上游主模型分片 | {gb(v['original_bytes'])} |
| 完全不变的模型主体 | {gb(body)} |
| 上游 Engram 表 | {gb(v['original_bytes']-body)} |
| 本版本 Q3_K 表 | {gb(tab)} |
| **本版本主分片合计** | **{gb(v['main_bytes'])}** |
| **减少** | **{gb(saved)}** |

直接主体来源为 [{v['source_repo']}](https://huggingface.co/{v['source_repo']})，固定版本 `{v['source_revision']}`。原始模型为 [{p['original_repo']}](https://huggingface.co/{p['original_repo']})，版本 `{p['original_revision']}`。Q3 数据来自已有 Sakura Maya-S 表，其输入为 Maya-S Q6_K；本次只适配表头，不再次量化模型主体或 Q3 数据。

完整保留 768,022,850 行，每行 256 值、110 字节。层 1/14 分别有 384,006,168 / 384,016,682 行。主体分片大小及 SHA-256 与上游一致；发布后的表头和 192 行真实 Q3 数据已核对。查找地址、哈希参数及完整 token map 按相应布局检查。

下载时将 {count} 个编号 GGUF 放在一起，从第一个分片加载。{'需要指定版本的 Project Maya 和本仓库 Q3 补丁，Maya-XS 依赖新版 IQ1 支持。' if maya else '需要支持 Unsloth DeepSeek-4.1 布局的指定 llama.cpp 分支。'} 固定运行时版本：`{v['runtime_revision']}`。详见上方加载说明。

**未进行完整模型推理测试。** 没有本版本的回答质量、困惑度、速度、GPU 执行、Windows 或 AMD 合格结论。源模型分数不能直接移用；文件大小不等于内存需求。文件校验和、许可、检查边界和其他 Sakura 版本比较见上方英文说明及清单。

</details>
'''

def overview(p,revisions):
 revrows='\n'.join(f"| [{v['variant']}](https://huggingface.co/{v['repo']}) | `{revisions[v['repo']]}` | {len(v['backbone'])+len(v['tables'])} |" for v in sorted(p['variants'],key=lambda x:x['main_bytes']))
 return f'''---
license: mit
language:
- en
- zh
tags:
- sakura
- deepseek
- engram
- model-overview
---
# Sakura DeepSeek-V4.1-Flash-1017 · Overview

**Eleven completed GGUF packages with unchanged upstream backbones and full Q3_K Engram tables.** This repository is the catalog; download weights from a linked variant.

**No full inference test has been performed on these modified packages.** The checks cover integrity, layout, addressing and isolated decoder paths. There are no Sakura generation-quality, perplexity, speed or hardware-fit scores for these releases.

## Original versus Sakura

{comparison(p)}

GB = 10^9 bytes. Main GGUF files only; optional vision/projector, DSpark/drafter, imatrix and runtime files are outside these totals. Disk size is not memory consumption. A smaller row is not proof of better quality. The original safetensors checkpoint's broader package is about 510.297 GB; original Maya-S is 339.478 GB.

## What Sakura changes

Sakura copies the credited upstream backbone files with identical sizes and full LFS SHA-256 identities, retains every expert and Engram row, and supplies the full lookup data in Q3_K. Q3_K applies to the tables only. No pruning, retraining or new backbone quantization is performed.

The shared lookup payload is 768,022,850 rows × 256 values, 110 bytes per row: **84,482,513,500 bytes** before small GGUF headers. Maya has separate layer 1/14 table files; Unsloth has one combined table. Header and runtime contracts differ; payload reuse does not make complete files interchangeable.

## Runtime and verification

- **Maya-S / Maya-XS:** use the exact Project Maya revision and source patch in the model card. The new Maya-XS route needs v1.1.22's IQ1 backbone support. CPU parity and CUDA compilation do not constitute a GPU or Windows/AMD inference test.
- **Unsloth:** use the pinned DeepSeek-4.1 llama.cpp branch in each model card; arbitrary stock runtimes are not qualified.

Every linked package was checked for main-file sizes/SHA-256, actual table headers and 192 real Q3 rows across both layers. Header repacks check their complete existing Q3 input and native-upload output hash. Read each build/compatibility record for exact scope.

## Pinned verified releases

| Variant | Verified model-card revision | Main GGUF files |
|---|---|---:|
{revrows}

## Sources and license

Original: [{p['original_repo']}](https://huggingface.co/{p['original_repo']}) at `{p['original_revision']}`. Backbones: [peasantsmith Maya](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF) and [Unsloth](https://huggingface.co/unsloth/DeepSeek-V4.1-Flash-1017-GGUF). Lookup source: [existing Sakura Maya-S Q3_K](https://huggingface.co/{p['split_sources']['repo']}). Runtime/format credits: Project Maya, GGML and llama.cpp. Relevant MIT notices remain with the model packages.

Free public standard CPU runners only; no paid runner/GPU or inference API. Public HF storage remains best-effort, and quota-neutral cross-repository deduplication is not assumed.

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

本目录列出 **11 个已完成的 DeepSeek-V4.1-Flash-1017 GGUF 版本**。主体保留上游原始字节，所有专家及全部 Engram 行均保留，仅将查找表以 Q3_K 存储。主体量化配方由上游作者提供；Q3_K 不表示整个模型都是 3 位。

上表对比对应上游大小、不变的主体、本版本主分片合计及减少量，单位为十进制 GB。最小 Maya-XS 为 199.824 GB；最小 Unsloth IQ1_S 为 206.867 GB。可选视觉、草稿模型、imatrix 和运行时不计入主分片合计。磁盘大小不等于内存要求，也不是质量排名。

表共有 768,022,850 行，每行 256 值、110 字节，数据区为 84,482,513,500 字节。Maya 使用两层独立表，Unsloth 使用合并表；两者表头和运行时约定不同。请下载对应整套分片，使用模型卡指定的运行时。

已核对主文件大小和 SHA-256、实际表头及跨两层的 192 行真实 Q3 数据。**未进行完整模型推理测试**；没有这些修改版本的回答质量、困惑度、速度、GPU 执行或 Windows/AMD 合格结论。上游或其他模型分数不能直接移用。

本仓库仅为目录，不存放大模型权重。模型、许可、固定版本及详细检查边界见各模型卡。

</details>
'''
