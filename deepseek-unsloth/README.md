# DeepSeek 1017 Unsloth IQ1_S / IQ1_M with a shared Q3_K Engram table

Cloud-only implementation for two dedicated Sakura releases. The four pinned Unsloth backbone files remain byte-identical. The existing two Sakura Maya-S Q3_K payloads are concatenated, without requantization, into Unsloth's combined width-256 table. Both outputs reuse the same complete table file.

`plan.json` freezes input revisions, input hashes, table geometry, output paths and sizes. `evidence/addressing-check.json` records the bounded cloud compatibility checks. `fixtures.json` contains only tiny, public real-row test fixtures. `upstream/host_rows.cpp` is the isolated native host-gather implementation from danielhanchen/llama.cpp commit b72050d03ae14bb3cb5138ecefab3f3f65157d31 (MIT). `upstream/deepseek41_conversion.py` contains the inspected hash-constant helpers from that same commit, with unrelated imports removed.

Tests: `python prepare_fixtures.py`, `python test_assembly.py`, `python test_publish.py`; compile `test_host_rows.cpp` against the pinned GGML base library and run it with the `evidence` directory. These are format, streaming, addressing, and isolated CPU decoder checks; no full model inference or GPU test.

Full build is refused in Work/local execution. Only the isolated workflow on the existing public repository's standard `ubuntu-24.04` GitHub-hosted runner may use the explicitly provided HF_TOKEN secret. No full model caching, large disk file, model artifact, GPU, paid runner or inference API. The original Maya and Flash-Next release files and workflows are unchanged.
