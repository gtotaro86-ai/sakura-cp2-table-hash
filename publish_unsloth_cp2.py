"""Publish one Unsloth CP2 package on a free public GitHub runner.

Whole files are copied inside Hugging Face. Only the mixed second shard is
streamed from pinned remote ranges plus the existing CP2 payload. No payload
file is written to disk. Refuses to run outside GitHub Actions.
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from huggingface_hub import CommitOperationAdd, CommitOperationCopy, HfApi
from huggingface_hub.errors import RepositoryNotFoundError

REVISION = "766911a6b7369840a91dbcd95f9f997acaab6cd6"
UNSLOTH = "unsloth/Qwen3.8-Flash-Next-GGUF"
DONOR = "webmp3/Sakura-Qwen3.8-Flash-Next-Compact-47.6GiB-K512-CP2-v1-GGUF"
DONOR_REV = "9b8fef370b812b3fd33787869d553793517245cb"
CP2_FILE = "Sakura-Qwen3.8-Flash-Next-K512-Q2_0-CP2-v1-Experimental-00002-of-00002.gguf"
CP2_SHA = "cf520743395d47e54e5e15ef14eaafe3f07d231e6dad0f185ac527c5f6826ffc"
CP2_SIZE = 13440065184
LICENSE_REPO = "webmp3/Sakura-Qwen3.8-Flash-Next-Compact-IQ3_S-CP2-GGUF"
LICENSE_REV = "baa65681adde32f9bd4bec6607f61fac2ee00046"

VARIANTS = {
    "UD-IQ1_S": {
        "port": 18121,
        "alias": "sakura-flash-next-ud-iq1-s-cp2",
        "shard1": ("UD-IQ1_S/Qwen3.8-Flash-Next-UD-IQ1_S-00001-of-00003.gguf", 10946624, "88a1420825a9304063e882ada29d438263617f51ac8923d438d927496693bafd"),
        "shard2_size": 49990818368,
        "shard3": ("UD-IQ1_S/Qwen3.8-Flash-Next-UD-IQ1_S-00003-of-00003.gguf", 22544696352, "0e25ceaeb89b8a80aa973c6c0c7448943682f7408c2855b2ebd016b7643a861a"),
        "segments": [
            ("header", 0, 37856),
            ("unsloth", 37696, 364584960),
            ("cp2", 672, 13440064512),
            ("unsloth", 29164760896, 20826057472),
        ],
        "output_bytes": 34630744800,
        "total_bytes": 57186387776,
    },
    "UD-IQ1_M": {
        "port": 18122,
        "alias": "sakura-flash-next-ud-iq1-m-cp2",
        "shard1": ("UD-IQ1_M/Qwen3.8-Flash-Next-UD-IQ1_M-00001-of-00003.gguf", 10946624, "6584f289c808a486ac33aef20906774bcf6616785535c03b842072951e5112d2"),
        "shard2_size": 49988981792,
        "shard3": ("UD-IQ1_M/Qwen3.8-Flash-Next-UD-IQ1_M-00003-of-00003.gguf", 24538827360, "ae757ff9347651adacc7746f137d8c29b51f25cf6bb27cd49086ef45bd8cc203"),
        "segments": [
            ("header", 0, 36160),
            ("unsloth", 36000, 364584960),
            ("cp2", 672, 13440064512),
            ("unsloth", 29164759200, 20824222592),
        ],
        "output_bytes": 34628908224,
        "total_bytes": 59178682208,
    },
    "UD-Q2_K_XL": {
        "port": 18123,
        "alias": "sakura-flash-next-ud-q2-k-xl-cp2",
        "shard1": ("UD-Q2_K_XL/Qwen3.8-Flash-Next-UD-Q2_K_XL-00001-of-00003.gguf", 10946624, "a4f3b21e77353999829f2f767e9ac21ce9c71d29a74f2cc9eda48c9bf23c8b86"),
        "shard2_size": 49979779296,
        "shard3": ("UD-Q2_K_XL/Qwen3.8-Flash-Next-UD-Q2_K_XL-00003-of-00003.gguf", 28878402944, "ec8c106759fdf4f463039c34c0707718d7d8908d53d892bd4f002e71620803f9"),
        "segments": [
            ("header", 0, 32032),
            ("unsloth", 31840, 364584960),
            ("cp2", 672, 13440064512),
            ("unsloth", 29164755040, 20815024256),
        ],
        "output_bytes": 34619705760,
        "total_bytes": 63509055328,
    },
}


class RangeSource:
    def __init__(self, url, size):
        self.url = url
        self.size = size
        self.block = 8 << 20
        self.cached_start = -1
        self.cached = b""

    def read_at(self, pos, n):
        out = []
        while n:
            if not self.cached_start <= pos < self.cached_start + len(self.cached):
                take = min(self.block, self.size - pos)
                self.cached_start = pos
                self.cached = self._range(pos, take)
            offset = pos - self.cached_start
            piece = min(n, len(self.cached) - offset)
            out.append(self.cached[offset:offset + piece])
            pos += piece
            n -= piece
        return b"".join(out)

    def _range(self, pos, n):
        end = pos + n - 1
        last = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(self.url, headers={
                    "Range": f"bytes={pos}-{end}",
                    "Accept-Encoding": "identity",
                    "User-Agent": "sakura-unsloth-cp2-publish/1",
                })
                with urllib.request.urlopen(req, timeout=120) as response:
                    if response.status != 206:
                        raise ValueError("range not honored")
                    data = response.read(n + 1)
                    if len(data) != n:
                        raise ValueError("short range")
                    return data
            except Exception as exc:
                last = exc
                time.sleep(min(30, 2 ** attempt))
        raise last


class BytesSource:
    def __init__(self, data):
        self.data = data

    def read_at(self, pos, n):
        return self.data[pos:pos + n]


class VirtualFile(io.BufferedIOBase):
    def __init__(self, segments):
        super().__init__()
        self.segments = segments
        self.ends = []
        total = 0
        for source, start, size in segments:
            total += size
            self.ends.append(total)
        self.size = total
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if pos < 0:
            raise ValueError("bad seek")
        self.pos = pos
        return pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, max(0, self.size - self.pos))
        if n > (256 << 20):
            raise ValueError("single read too large")
        chunks = []
        while n:
            i = 0
            while i < len(self.ends) and self.ends[i] <= self.pos:
                i += 1
            seg_start = self.ends[i - 1] if i else 0
            source, offset, size = self.segments[i]
            take = min(n, size - (self.pos - seg_start))
            data = source.read_at(offset + self.pos - seg_start, take)
            if len(data) != take:
                raise EOFError("truncated source")
            chunks.append(data)
            self.pos += take
            n -= take
        return b"".join(chunks)


def repo_for(variant):
    return f"webmp3/Sakura-Qwen3.8-Flash-Next-Compact-{variant}-CP2-GGUF"


def dest_name(variant, index):
    return f"Sakura-Qwen3.8-Flash-Next-Compact-{variant}-CP2-Experimental-0000{index}-of-00003.gguf"


def readme(variant, spec):
    gib = spec["total_bytes"] / (1024 ** 3)
    repo = repo_for(variant)
    return f"""---
base_model:
- Qwen/Qwen3.8-Flash-Next
- unsloth/Qwen3.8-Flash-Next-GGUF
base_model_relation: quantized
license: other
license_name: qwen-community-1.0
license_link: LICENSE
library_name: gguf
pipeline_tag: text-generation
tags:
- gguf
- qwen4exp
- qwen3.8-flash-next
- unsloth
- sakura
- experimental
---

# Sakura Qwen3.8 Flash-Next Compact {variant} CP2

Experimental community repack of **Unsloth {variant}**, retaining all **512 routed experts**. Shards 1 and 3 are copied unchanged. Shard 2 keeps every non-table tensor and replaces only `per_layer_token_embd.weight` with the existing Sakura CP2 table.

**This exact {variant} + CP2 package has not been loaded for inference or tested for generation, perplexity, quality or speed.** Its pinned file hashes, GGUF split layout, lookup addressing and tokenizer metadata were checked before publication. This is an experimental structural release, not a model-quality or hardware qualification.

## Files and size

| Component | Bytes | GiB |
|---|---:|---:|
| Unsloth shard 1, metadata only | {spec['shard1'][1]:,} | {spec['shard1'][1] / 1024 ** 3:.3f} |
| Rebuilt shard 2, other weights plus existing CP2 table | {spec['output_bytes']:,} | {spec['output_bytes'] / 1024 ** 3:.3f} |
| Unsloth shard 3, remaining weights | {spec['shard3'][1]:,} | {spec['shard3'][1] / 1024 ** 3:.3f} |
| All three model files | {spec['total_bytes']:,} | **{gib:.3f}** |

File size is not GPU memory usage and is not proof that this configuration fits a particular machine. The backbone remains Unsloth's original mixed quantization. CP2 describes only the experimental table representation.

## Download and start on Windows

```text
hf download {repo} --local-dir Sakura-{variant}-CP2
```

Keep all three numbered GGUF files, `START.cmd` and the complete `runtime` directory together. Start `START.cmd`, wait for loading, then open **http://127.0.0.1:{spec['port']}**. The OpenAI-compatible endpoint is `/v1/chat/completions`, with alias `{spec['alias']}`. Stop the server with Ctrl+C.

The starter uses the included Windows x64 Vulkan CP2 runtime, one slot, context 4096, Q8 KV cache and lazy table reads. MTP, vision and the optional CP2 GPU row cache are disabled. This starter has not been executed against this exact package.

Use the included runtime. Stock llama.cpp, LM Studio, Ollama and unrelated forks are not qualified for this custom CP2 table. No AMD/64-GB-UMA fit, peak-memory, long-context or performance result is claimed.

## What was verified

- Shards 1 and 3 are identified by their full HF LFS SHA256 and copied without payload or metadata changes.
- The Unsloth table payload SHA256 of UD-IQ1_S matches the ISTA/IQ4_NL input used to build the existing CP2 table: `dd55c28902f38cd88134b2a569c51282c5ffce30080487e1a645740115c56cc3`. The three examined Unsloth tables were already identical to each other.
- The CP2 table is a lossy derivative, not byte-identical to that IQ4_NL input.
- Lookup addressing and raw tokenizer metadata matched the checked ISTA reference before this repack.
- The existing CP2 runtime is reused unchanged. No new encoder, training, expert pruning or runtime port was performed.

Previously reported Sakura Q2, ISTA Compact or Gyro scores are **not** results for this package. Model-file integrity after the server-side copy is checked against HF LFS hash and size metadata.

## Hardware compatibility

The supplied binaries are the same Windows x64 Vulkan CP2 runtime as [Sakura K512 CP2](https://huggingface.co/{DONOR}). Vulkan support in a GPU driver alone does not establish compatibility. **This exact Unsloth + CP2 weight combination has not been loaded.** No speed, fit or quality number from K512, ISTA Compact or Gyro is a result for this package.

| Hardware / platform | Status | What to expect |
|---|---|---|
| AMD Strix Halo, Radeon 8060S, 64 GB UMA, Windows x64 | Runtime tested on the K512 CP2 package only | Same supplied runtime. This Unsloth package is larger ({gib:.1f} GiB of model files) and has not been loaded here. |
| Other Strix Halo configurations | Not tested | Similar hardware is not a separate validation. |
| Other AMD, NVIDIA or Intel GPUs | Not tested | No CUDA build is supplied. No hardware-specific profile has been qualified. |
| GPUs with 24 or 32 GB dedicated VRAM | Default profile not validated | Disk size is not running memory. A smaller card may need different offloading; such profiles have not been tested. |
| CPU-only, Linux, macOS, Windows on ARM | No matching native binary supplied | This package contains Windows x64 binaries. |

Storage: allow at least the model files plus the runtime. An SSD is recommended for the lazily read table.

[简体中文](README_zh.md)

## Provenance and license

Base: [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next). Direct backbone: [unsloth/Qwen3.8-Flash-Next-GGUF](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF), revision `{REVISION}`. Existing CP2 table and matching runtime: [Sakura K512 CP2](https://huggingface.co/{DONOR}), revision `{DONOR_REV}`.

Credit for the Unsloth quantization belongs to Unsloth and its contributors; credit for Qwen belongs to Qwen. Sakura supplies the experimental lookup-table representation and this repack. This release claims no authorship of the backbone, no retraining and no endorsement by those projects.

Model weights retain **Qwen Community License 1.0**, included in `LICENSE` and `LICENSE-QWEN`. Read its complete conditions before use. Runtime software has its separate notices under `runtime/`; software licensing does not relicense model weights.
"""


def readme_zh(variant, spec):
    gib = spec["total_bytes"] / (1024 ** 3)
    repo = repo_for(variant)
    return f"""[English](README.md) | 简体中文 | Sakura = 樱花 (yīnghuā)

# Sakura — Qwen3.8-Flash-Next Compact {variant} CP2

这是 **Unsloth {variant}** 的实验性社区重打包,保留全部 **512** 个路由专家。分片 1 和 3 原样复制。分片 2 保留表以外的全部张量,只把 `per_layer_token_embd.weight` 换成已有的 Sakura CP2 表。

**这个 {variant} + CP2 组合没有做过推理加载,也没有生成、困惑度、质量或速度测试。** 这是结构发布,不是质量或硬件认证。

三个模型文件合计 **{gib:.3f} GiB**。文件大小不是运行内存。32 GB 或 24 GB 显卡不能从文件大小推断为可以运行。

```text
hf download {repo} --local-dir Sakura-{variant}-CP2
```

三个编号 GGUF、`START.cmd` 和完整 `runtime` 目录必须放在一起。运行 `START.cmd`,然后打开 **http://127.0.0.1:{spec['port']}**。别名 `{spec['alias']}`。请使用附带的 Windows x64 Vulkan CP2 运行时。普通 llama.cpp、LM Studio 和 Ollama 未针对这个自定义 CP2 表验证。

## 硬件兼容性

附带的二进制文件与 [Sakura K512 CP2](https://huggingface.co/{DONOR}) 相同。仅有 Vulkan 驱动并不等于兼容。**这个 Unsloth + CP2 权重组合尚未加载。** K512、ISTA Compact 或 Gyro 的速度和适配数字不是本包的结果。

| 硬件 / 平台 | 状态 | 预期 |
|---|---|---|
| AMD Strix Halo, Radeon 8060S, 64 GB UMA, Windows x64 | 仅 K512 CP2 包测试过该运行时 | 运行时相同。本包更大({gib:.1f} GiB),尚未在此加载。 |
| 其他显卡、仅 CPU、Linux、macOS、ARM 版 Windows | 未测试或没有对应的本机二进制 | 本包只含 Windows x64 二进制。 |

骨干:[unsloth/Qwen3.8-Flash-Next-GGUF](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF),修订 `{REVISION}`。权重保留 Qwen Community License 1.0。
"""


def starter(variant, spec):
    name = dest_name(variant, 1)
    return f"""@echo off
setlocal
set "SAKURA_CP_OVERLAY="
set "SAKURA_CP_TRACE="
set "SAKURA_CP2_GPU_CACHE_MIB=0"
"%~dp0runtime\\llama-server.exe" -m "%~dp0{name}" --host 127.0.0.1 --port {spec['port']} --alias {spec['alias']} --parallel 1 --device Vulkan0 -ngl 99 -c 4096 -b 256 -ub 256 -fa on -ctk q8_0 -ctv q8_0 -lm dio --lazy-mode on --jinja --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.05
if errorlevel 1 pause
"""


def lfs_file(info, path):
    found = next(f for f in info.siblings if f.rfilename == path)
    if not found.lfs:
        raise ValueError("expected LFS file: " + path)
    return found


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Refusing local execution; this would transfer tens of gigabytes")
    if os.environ.get("GITHUB_REPOSITORY_VISIBILITY", "public") == "private":
        raise SystemExit("Private runner minutes are not used")
    variant = sys.argv[1]
    spec = VARIANTS[variant]
    repo = repo_for(variant)
    api = HfApi()
    who = api.whoami()
    if who.get("name") != "webmp3" or who.get("isPro"):
        raise SystemExit("Unexpected HF account")
    created = False
    try:
        api.model_info(repo)
    except RepositoryNotFoundError:
        api.create_repo(repo, repo_type="model", private=False, exist_ok=False)
        created = True
    header = Path("headers") / f"{variant}.bin"
    header_bytes = header.read_bytes()
    if len(header_bytes) != spec["segments"][0][2]:
        raise SystemExit("header length mismatch")
    unsloth = api.model_info(UNSLOTH, revision=REVISION, files_metadata=True)
    donor = api.model_info(DONOR, revision=DONOR_REV, files_metadata=True)
    if unsloth.private or donor.private:
        raise SystemExit("source repo is not public")
    shard2_name = spec["shard1"][0].replace("00001", "00002")
    remote2 = lfs_file(unsloth, shard2_name)
    remote_cp2 = lfs_file(donor, CP2_FILE)
    if remote2.size != spec["shard2_size"] or remote_cp2.lfs.sha256 != CP2_SHA or remote_cp2.size != CP2_SIZE:
        raise SystemExit("pinned source mismatch")
    unsloth_url = f"https://huggingface.co/{UNSLOTH}/resolve/{REVISION}/{shard2_name}"
    cp2_url = f"https://huggingface.co/{DONOR}/resolve/{DONOR_REV}/{CP2_FILE}"
    sources = {
        "header": BytesSource(header_bytes),
        "unsloth": RangeSource(unsloth_url, remote2.size),
        "cp2": RangeSource(cp2_url, remote_cp2.size),
    }
    segments = []
    for kind, start, length in spec["segments"]:
        segments.append((sources[kind], start, length))
    virtual = VirtualFile(segments)
    if virtual.size != spec["output_bytes"]:
        raise SystemExit("segment total mismatch")
    print(json.dumps({"uploading_shard2": spec["output_bytes"], "variant": variant}), flush=True)
    api.upload_file(
        path_or_fileobj=virtual,
        path_in_repo=dest_name(variant, 2),
        repo_id=repo,
        commit_message=f"Add rebuilt {variant} CP2 shard 2",
    )
    operations = []
    expected = {}
    for index, item in ((1, spec["shard1"]), (3, spec["shard3"])):
        path, size, digest = item
        found = lfs_file(unsloth, path)
        if found.size != size or found.lfs.sha256 != digest:
            raise SystemExit("shard hash mismatch: " + path)
        operations.append(CommitOperationCopy(
            src_repo_id=UNSLOTH, src_repo_type="model", src_revision=REVISION,
            src_path_in_repo=path, path_in_repo=dest_name(variant, index),
        ))
        expected[dest_name(variant, index)] = (digest, size)
    for sibling in donor.siblings:
        if sibling.rfilename.startswith("runtime/"):
            operations.append(CommitOperationCopy(
                src_repo_id=DONOR, src_repo_type="model", src_revision=DONOR_REV,
                src_path_in_repo=sibling.rfilename, path_in_repo=sibling.rfilename,
            ))
    license_info = api.model_info(LICENSE_REPO, revision=LICENSE_REV, files_metadata=True)
    for name in ("LICENSE", "LICENSE-QWEN", "NOTICE.md"):
        if any(f.rfilename == name for f in license_info.siblings):
            operations.append(CommitOperationCopy(
                src_repo_id=LICENSE_REPO, src_repo_type="model", src_revision=LICENSE_REV,
                src_path_in_repo=name, path_in_repo=name,
            ))
    docs = {
        "README.md": readme(variant, spec).encode("utf8"),
        "README_zh.md": readme_zh(variant, spec).encode("utf8"),
        "START.cmd": starter(variant, spec).replace("\n", "\r\n").encode("utf8"),
        "results.json": json.dumps({
            "variant": variant,
            "source_repo": UNSLOTH,
            "source_revision": REVISION,
            "donor_revision": DONOR_REV,
            "output_bytes": spec["total_bytes"],
            "model_loaded_for_inference": False,
            "generation_tested": False,
            "ppl_tested": False,
            "speed_tested": False,
            "hardware_fit_tested": False,
            "quality_note": "No scores from other quantizations are transferred to this release.",
        }, indent=2).encode("utf8"),
        "PROVENANCE.json": json.dumps({
            "backbone": UNSLOTH,
            "revision": REVISION,
            "cp2_table": {"repo": DONOR, "revision": DONOR_REV, "file": CP2_FILE, "sha256": CP2_SHA},
            "table_payload_sha256": "dd55c28902f38cd88134b2a569c51282c5ffce30080487e1a645740115c56cc3",
        }, indent=2).encode("utf8"),
    }
    for name, data in docs.items():
        operations.append(CommitOperationAdd(path_in_repo=name, path_or_fileobj=data))
    commit = api.create_commit(
        repo_id=repo,
        operations=operations,
        commit_message=f"Publish Compact {variant} CP2 experimental repack",
        commit_description="Copy unchanged Unsloth shards and existing CP2 runtime. Shard 2 was streamed from pinned ranges. No inference validation is claimed.",
    )
    after = HfApi(token=False).model_info(repo, revision=commit.oid, files_metadata=True)
    if after.private:
        raise SystemExit("repository is not public")
    shard2 = lfs_file(after, dest_name(variant, 2))
    if shard2.size != spec["output_bytes"]:
        raise SystemExit("uploaded shard 2 size mismatch")
    for name, (digest, size) in expected.items():
        found = lfs_file(after, name)
        if found.size != size or found.lfs.sha256 != digest:
            raise SystemExit("copied shard mismatch: " + name)
    receipt = {
        "variant": variant,
        "repo": repo,
        "revision": commit.oid,
        "public": True,
        "shard2_sha256": shard2.lfs.sha256,
        "shard2_bytes": shard2.size,
        "model_bytes": spec["total_bytes"],
        "inference_tested": False,
        "paid": False,
    }
    print(json.dumps(receipt), flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text("```json\n" + json.dumps(receipt, indent=2) + "\n```\n", encoding="utf8")


if __name__ == "__main__":
    main()
