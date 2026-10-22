"""Prepare metadata-only updates for the two newer Flash-Next Unsloth CP2 builds."""
import json,hashlib,urllib.request,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
up=json.loads((HERE/'flash/upstream-info.json').read_text());targets=[]
for folder in sorted((HERE/'flash').glob('Sakura-*')):
 info=json.loads((folder/'info.json').read_text());result=json.loads((folder/'results.json').read_text());prov=json.loads((folder/'PROVENANCE.json').read_text());q=result['variant'];repo=info['id']
 src=[f for f in up['siblings'] if f['rfilename'].startswith(q+'/') and f['rfilename'].endswith('.gguf')];out=[f for f in info['siblings'] if f['rfilename'].endswith('.gguf')]
 old=sum(f['size'] for f in src);new=sum(f['size'] for f in out);assert new==result['output_bytes'];saved=old-new
 cp=13440064512;original_table=28800138240
 # Source/data identities stay intact; private build links and superseded repository names are removed.
 prov.pop('build_workflow',None)
 for key in ['run_url','run_head_sha']:prov.get('input_identity_proof',{}).pop(key,None)
 prov['cp2_table']['repo']='webmp3/Sakura-Qwen3.8-Flash-Next-Compact-ISTA-Q2_0-512E-CP2-GGUF'
 prov['documentation_update']={'scope':'English comparison and collapsed Chinese; no weight, runtime, starter or model-name change','private_build_links_omitted':True,'model_inference_tested':False}
 cn=f'''# Sakura Qwen3.8 Flash-Next · Unsloth {q} · 512E · CP2

本版本主体直接来自 Unsloth `{q}`，保留全部 512 个路由专家。第 1、3 分片逐字节不变；第 2 分片保留其他权重，仅将 n-gram/PLE 表替换为已有 Sakura CP2 数据。

| 内容 | 十进制 GB |
|---|---:|
| 对应 Unsloth 原始三分片 | {old/1e9:.3f} |
| 原始 IQ4_NL 表数据区 | {original_table/1e9:.3f} |
| CP2 表数据区 | {cp/1e9:.3f} |
| **本版本三个主分片** | **{new/1e9:.3f}** |
| **净减少** | **{saved/1e9:.3f}** |

全部文件合计 {new:,} 字节，即 {new/1024**3:.3f} GiB；不含运行时和小型说明文件。文件大小不等于显存或内存用量。**本权重组合未进行完整推理、生成、困惑度、速度或硬件适配测试。** 其他 Sakura 模型的分数不可移用。

模型主体来源：`{result['source_repo']}`，版本 `{result['source_revision']}`。CP2 数据和对应 Windows x64 Vulkan 运行时来自 [Sakura ISTA Q2_0 512E CP2](https://huggingface.co/{prov['cp2_table']['repo']})，版本 `{result['donor_revision']}`。保留 Qwen Community License 1.0 及运行时独立许可。

下载完整仓库，将三个编号 GGUF、`START.cmd` 及完整 `runtime` 文件夹保持在一起，运行 `START.cmd`。CP2 是自定义查找表格式，需要随附运行时。这个 Unsloth 版本本身没有在 64 GB Strix Halo 上完成加载或运行验证。

已核对原始分片 1/3 和运行时的 HF 文件 SHA-256；重建分片 2 的表头、形状、偏移及少量表内/表外字节经过检查。2026-10-22 的复核没有独立下载并重哈希完整重建分片。输入 IQ4_NL 与输出 CP2 的哈希在 `PROVENANCE.json` 中分开记录。
'''
 text=f'''---
base_model: {result['source_repo']}
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
# Sakura Qwen3.8 Flash-Next Compact · Unsloth {q} · 512E · CP2

Community repack of **Unsloth {q}**, retaining all **512 routed experts**. Shards 1 and 3 are unchanged. Shard 2 preserves its other weights and replaces only `per_layer_token_embd.weight` with the existing Sakura CP2 lookup data.

**This exact {q} + CP2 package has not been loaded for inference or tested for generation, perplexity, quality, speed or hardware fit.** The integrity/structural checks below do not establish model quality or transfer another Sakura package's results.

## Original versus Sakura

| Component / comparison | Bytes | Decimal GB | GiB |
|---|---:|---:|---:|
| Original matching Unsloth three-shard set | {old:,} | {old/1e9:.3f} | {old/1024**3:.3f} |
| Original IQ4_NL table payload | {original_table:,} | {original_table/1e9:.3f} | {original_table/1024**3:.3f} |
| Existing CP2 table payload | {cp:,} | {cp/1e9:.3f} | {cp/1024**3:.3f} |
| **Sakura three main GGUFs** | **{new:,}** | **{new/1e9:.3f}** | **{new/1024**3:.3f}** |
| **Net saving against matching Unsloth** | **{saved:,}** | **{saved/1e9:.3f}** | **{saved/1024**3:.3f}** |

Raw table-payload saving is {original_table-cp:,} bytes. Rebuilt GGUF metadata adds 160 bytes, giving the net saving shown above. Runtime, starter and documentation are additional. Disk size is not memory consumption or proof that a package fits your GPU/UMA.

| GGUF shard | Original bytes | Sakura bytes | Treatment |
|---|---:|---:|---|
'''
 for i,(a,b) in enumerate(zip(sorted(src,key=lambda f:f['rfilename']),sorted(out,key=lambda f:f['rfilename'])),1):text+=f"| {i} | {a['size']:,} | {b['size']:,} | {'Copied unchanged' if i in [1,3] else 'Table replaced; other weights retained'} |\n"
 port=int(re.search(r'127\.0\.0\.1:(\d+)',(folder/'README.md').read_text()).group(1))
 text+=f'''
## Download and start on Windows

```text
hf download {repo} --local-dir Sakura-{q}-CP2
```

Keep all three numbered GGUFs, `START.cmd` and the complete `runtime` directory together. Start `START.cmd`, then open **http://127.0.0.1:{port}**. The OpenAI-compatible endpoint is `/v1/chat/completions`.

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

Original model: [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next). Direct backbone: [{result['source_repo']}](https://huggingface.co/{result['source_repo']}), revision `{result['source_revision']}`. Existing CP2 data and runtime: [Sakura ISTA Q2_0 512E CP2](https://huggingface.co/{prov['cp2_table']['repo']}), revision `{result['donor_revision']}`.

The backbone recipe belongs to Unsloth; Qwen belongs to Qwen. Sakura supplies the lookup-table representation and repack, without claiming retraining, upstream authorship or endorsement. Model weights retain **Qwen Community License 1.0**, included in `LICENSE` / `LICENSE-QWEN`. Runtime software has its own MIT/third-party notices; those do not relicense the weights.

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

{cn}
</details>
'''
 outdir=HERE/'flash-docs'/q;outdir.mkdir(parents=True,exist_ok=True)
 changes={'README.md':text.encode(),'README_zh.md':cn.encode(),'PROVENANCE.json':(json.dumps(prov,indent=2)+'\n').encode()}
 url=f"https://huggingface.co/{repo}/resolve/{info['sha']}/SHA256SUMS"
 with urllib.request.urlopen(url,timeout=30) as response:sums=response.read(200001)
 if len(sums)>200000:raise RuntimeError('Small checksum cap')
 lines=[]
 for line in sums.decode().splitlines():
  parts=line.split(None,1)
  if len(parts)==2:
   path=parts[1].lstrip('* ')
   if path in changes:line=hashlib.sha256(changes[path]).hexdigest()+'  '+path
  lines.append(line)
 changes['SHA256SUMS']=('\n'.join(lines)+'\n').encode()
 for name,b in changes.items():
  if b'gtotaro86' in b.lower() or b'sakura-cp2-table-hash' in b.lower():raise RuntimeError('Personal build reference')
  (outdir/name).write_bytes(b)
 locked=[{'path':f['rfilename'],'size':f['size'],'sha256':(f.get('lfs') or {}).get('sha256'),'blob_id':f.get('blobId')} for f in info['siblings'] if f['rfilename'] not in changes]
 targets.append({'repo':repo,'source_revision':info['sha'],'variant':q,'main_bytes':new,'locked_files':locked,'documents':list(changes)})
(HERE/'flash-doc-plan.json').write_text(json.dumps(targets,indent=2)+'\n')
print(json.dumps({'prepared_flash_cards':len(targets),'weights_runtime_starters_unchanged':True}),flush=True)
