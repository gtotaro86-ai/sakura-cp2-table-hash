"""English model card with default-collapsed Simplified Chinese translation."""
def make_card(plan,v,record):
 quant=v['quant'];main=v['main_bytes'];old=v['upstream_main_bytes'];body=sum(x['size'] for x in v['backbone']);table=record['size'];saved=old-main
 rows='\n'.join(f"| `{f['path']}` | {f['size']:,} | `{f['sha256']}` |" for f in v['backbone']+[{'path':v['table_path'],'size':table,'sha256':record['sha256']}])
 return f'''---
license: mit
base_model: {plan['upstream_repo']}
base_model_relation: quantized
pipeline_tag: text-generation
language:
- en
- zh
tags:
- gguf
- deepseek
- engram
- q3_k
- unsloth
- mixture-of-experts
---
# Sakura DeepSeek-V4.1-Flash-1017 — Unsloth {quant} + Engram Q3_K

**Unchanged Unsloth {quant} backbone, with the full Engram lookup table stored in Q3_K.**

**No full inference test has been performed.**

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

## 模型与来源

本仓库保留 Unsloth `{quant}` 的四个模型主体分片，逐字节不变；只将 Engram 查找表替换为 Q3_K。这里的 Q3_K **仅指 Engram 表**，并不表示整个模型都是 3 位。

原始模型为 [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017)，修订版本 `1bae0e1088993b9b82de08f59de5be5a34e42170`。模型主体直接来自 [{plan['upstream_repo']}](https://huggingface.co/{plan['upstream_repo']})，固定修订版本 `{plan['upstream_revision']}`。

Engram 表来自已完成的 [Sakura Maya-S Q3_K 版本](https://huggingface.co/{plan['q3_source_repo']})，修订版本 `{plan['q3_source_revision']}`。该表由 peasantsmith 的 Maya-S Q6_K 表重新量化为 Q3_K，Maya 输入修订版本为 `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`。本次构建将两层已有 Q3_K 数据按层 1、层 14 的顺序拼接，并生成 Unsloth 所需的单一 GGUF 张量；没有再次量化 Q3_K 数据，也没有从 IQ4_NL 表再次量化。

## 大小比较

| 内容 | 十进制 GB |
|---|---:|
| 原始 Unsloth {quant} 五个主分片 | {old/1e9:.3f} |
| 保持不变的 Unsloth 模型主体 | {body/1e9:.3f} |
| 原始 Unsloth IQ4_NL Engram 表 | {v['upstream_table']['size']/1e9:.3f} |
| 本版本 Q3_K Engram 表 | {table/1e9:.3f} |
| 本版本五个主分片合计 | **{main/1e9:.3f}** |
| 相比对应 Unsloth 版本减少 | **{saved/1e9:.3f}** |

主分片合计为 **{main:,} 字节（{main/(1024**3):.3f} GiB）**。独立视觉投影器和 DSpark 草稿模型不在该合计中。磁盘文件大小不等于运行时内存需求；本版本没有在 64 GB Strix Halo 上完成运行验证。

## 表格式与兼容性

完整保留 768,022,850 行，每行 256 个值。层 1 有 384,006,168 行，层 14 有 384,016,682 行；第二层在合并表中的起始行是 384,006,168。每行一个 Q3_K 块，110 字节；总数据区为 84,482,513,500 字节，加上 192 字节 GGUF 头。类型为真实的 GGML 类型 11，未将其他格式伪装为 Q6_K。

保持 Unsloth 的 `per_layer_token_embd.weight` 名称、五分片结构、1043 张量总数和原有哈希地址元数据。请将对应目录中的五个分片放在一起，并从 `-00001-of-00005.gguf` 加载。

需要支持该 Unsloth DeepSeek-4.1 格式的运行时。检查所针对的源码为 [danielhanchen/llama.cpp](https://github.com/danielhanchen/llama.cpp/tree/{plan['runtime_revision']})，提交 `{plan['runtime_revision']}`，对应 [PR #30817](https://github.com/ggml-org/llama.cpp/pull/30817)。本仓库没有证明所有 llama.cpp、LM Studio 或 Maya 版本都可直接加载它。

## 验证与限制

已检查：固定输入的文件大小与 SHA-256；两个来源中 192 行 Q6_K 真实样本逐字节相同；Unsloth 的层顺序、48 个哈希桶大小与偏移及哈希乘数；隔离的原生 CPU Q3_K 行读取路径，对 192 行真实样本、两层边界、最后一行和 64 位文件偏移进行了位精确比较；实际 HF 文件对象的哈希、多段上传、回绕读取以及损坏源拒绝测试。原生 Xet 流式上传会在发布文件引用之前验证两个 Q3_K 源文件的完整 SHA-256，以及发布后的五个分片大小和 SHA-256。

**未进行完整模型推理测试。** 未进行本版本的困惑度、任务质量、GPU 运行或 Windows/AMD 测试。小样本行误差不能当作模型质量。改变 Engram 精度后，上游 Unsloth 或 Maya 的质量分数不能直接沿用。

完整构建在免费的公共标准 CPU runner 中流式完成，不需要用户电脑下载模型，没有 GPU、付费 runner 或推理 API。IQ1_S 与 IQ1_M 共享同一份字节完全相同的合并表；未承诺 HF 的存储去重会免除配额占用。

文件列表、校验和及构建记录见下方英文表格和 [build-manifest.json](build-manifest.json)。兼容性记录：[compatibility-check.json](compatibility-check.json)。DeepSeek、Unsloth、Project Maya 与 GGML 的相关许可和署名均应保留；本仓库附带 MIT 许可文本。

</details>

## Provenance and exact changes

- Original model: [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), revision `1bae0e1088993b9b82de08f59de5be5a34e42170`.
- Direct backbone source: [{plan['upstream_repo']}](https://huggingface.co/{plan['upstream_repo']}), revision `{plan['upstream_revision']}`, variant `{quant}`. All four backbone files, including the metadata shard, are copied server-side with identical sizes and SHA-256 hashes.
- Table source: [{plan['q3_source_repo']}](https://huggingface.co/{plan['q3_source_repo']}), revision `{plan['q3_source_revision']}`. Its existing Q3_K payloads were originally quantized from [peasantsmith's Maya-S Q6_K tables](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF) at `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`, using GGML `{plan['reference_ggml_revision']}`.
- This build **repacks the existing Q3_K payloads without changing their bits**, in layer 1 then layer 14 order, into Unsloth's combined `per_layer_token_embd.weight`. It does not requantize the upstream IQ4_NL table or quantize the backbone again.

The `{quant}` label describes the existing mixed Unsloth backbone recipe. **Q3_K describes only the Engram table.** All rows and experts are retained.

## Size comparison

| Package / component | Decimal GB | Scope |
|---|---:|---|
| Official 1017 safetensors checkpoint | 510.297 | Broader package, including additional components; not a scope-matched reduction baseline |
| Original Maya-S | 339.478 | Six main GGUF shards |
| Existing Sakura Maya-S + Q3_K Engram | 262.676 | Six main GGUF shards |
| Original Unsloth {quant} | {old/1e9:.3f} | Five main GGUF shards |
| Unchanged {quant} backbone | {body/1e9:.3f} | First four shards |
| Original IQ4_NL table | {v['upstream_table']['size']/1e9:.3f} | Fifth upstream shard |
| New combined Q3_K table | {table/1e9:.3f} | Fifth Sakura shard |
| **This release** | **{main/1e9:.3f}** | Five main GGUF shards |
| **Saving versus the matching Unsloth variant** | **{saved/1e9:.3f} ({100*saved/old:.2f}%)** | Same main-shard scope |

Total: **{main:,} bytes = {main/(1024**3):.3f} GiB**. Optional vision-projector and DSpark files are separate and are not included in this total. These are disk sizes, not RAM/VRAM requirements. This release has not been qualified on a 64 GB Strix Halo.

## Table geometry and addressing

| Property | Value |
|---|---|
| Layer order | 1, then 14 |
| Rows per layer | 384,006,168 / 384,016,682 |
| Total rows | 768,022,850 |
| Values per row | 256 |
| Row storage | One Q3_K block, 110 bytes |
| Payload | 84,482,513,500 bytes |
| Complete table GGUF | {table:,} bytes, including its 192-byte header |
| Actual GGML type | 11 / Q3_K |
| Tensor | `per_layer_token_embd.weight` |
| Second-layer starting row | 384,006,168 |
| Split metadata | Shard 5 of 5; 1,043 tensors across the set |

No dtype relabeling or row padding is used. Unsloth's original tokenizer/hash metadata stays byte-identical in its metadata shard.

## Runtime and loading

Keep all five files of `{quant}/` together and load its `-00001-of-00005.gguf` file. A runtime supporting **this Unsloth DeepSeek-4.1 layout** is required.

The inspected runtime is [danielhanchen/llama.cpp](https://github.com/danielhanchen/llama.cpp/tree/{plan['runtime_revision']}) at `{plan['runtime_revision']}`, from [llama.cpp PR #30817](https://github.com/ggml-org/llama.cpp/pull/30817). Its host gather dispatches through the actual Q3_K decoder. The isolated native path was checked; this is not a claim that arbitrary stock llama.cpp, LM Studio, or Maya builds support this package.

The upstream [Unsloth guide](https://unsloth.ai/docs/models/deepseek-v4.1-flash) describes the combined table and lazy CPU lookup path. Full runtime loading, GPU execution, Windows/AMD behavior, and performance of this modified model remain untested.

## Verification and quality status

- Pinned input metadata and all unchanged backbone sizes/SHA-256 hashes checked.
- 192 real Q6_K sample rows matched byte-for-byte between Maya and Unsloth, across the beginning, middle and end of both layers. This sample comparison alone does not establish full source-payload identity.
- Layer order, all 48 bucket sizes/absolute offsets, and hash multipliers match the pinned converter and Unsloth metadata.
- Isolated native host-gather tests returned bit-identical decoded values for 192 real Q3_K rows, including layer boundaries, final rows, reversed gathers and 64-bit byte offsets.
- The seekable stream passed real HF 2.2.0 hashing/multipart/rewind tests with simulated transport. The native hf-xet 1.7.0 streaming path passed actual local-CAS checks, corruption/length rejection tests, and a small real cloud upload/download check before reading the full table.
- Native Xet streaming checked both complete source Q3_K file hashes and the independently recorded combined SHA-256 before publishing the file reference. All five published file sizes and SHA-256 hashes were checked after finalization.

**No full inference test has been performed.** No model-level perplexity, coding, answer-quality, GPU or Windows/AMD test is reported for this release. Sample row error is not model quality. Upstream Unsloth/Maya scores cannot be transferred to the changed Engram table.

## Files and reproducibility

| File | Bytes | SHA-256 |
|---|---:|---|
{rows}

Build record: [build-manifest.json](build-manifest.json). Compatibility evidence: [compatibility-check.json](compatibility-check.json).

The build uses a free public standard CPU runner and bounded-memory streaming. It needs no model download on the user's PC, no GPU, paid runner or inference API. The same combined table is reused byte-identically between IQ1_S and IQ1_M; no quota-neutral HF deduplication is assumed. Public free storage remains subject to HF's best-effort limits.

## Credits and license

DeepSeek-AI: original model and Engram. Unsloth: existing mixed-precision backbone. peasantsmith / Project Maya: Q6_K table source. GGML / llama.cpp: reference Q3_K quantizer and reader. Sakura: table repack, compatibility checks and release assembly.

MIT; retain relevant upstream notices. Included texts: [LICENSE.DeepSeek](LICENSE.DeepSeek) and [LICENSE.ggml](LICENSE.ggml).
'''
