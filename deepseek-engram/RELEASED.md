# Sakura DeepSeek Engram Q3_K — released

The complete cloud build and publication finished successfully on 22 October 2026 at 08:57 Europe/Berlin, after 1 hour 27 minutes 29 seconds. Both table builds ran in parallel on standard public Ubuntu CPU runners. No paid runner, GPU or inference API was used.

Model: https://huggingface.co/webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF

Pinned release revision: `4a701f59f623b08a859368926cd9a210ab446941`.

The six GGUF sizes and Hub LFS SHA256 values were checked directly against the build manifest. The first four backbone files match the original source hashes. Both published 192-byte table headers match the expected Q3_K headers (type 11). The runtime patch matches the previously checked source patch. This final independent check read only 384 model bytes.

Total GGUF size: 262,675,668,988 bytes; Q3 table payload: 84,482,513,500 bytes. Reduction from original main model: 76,802,285,000 bytes.

The included Maya Q3_K Engram patch is required. CUDA compilation and scalar/reader/stream checks were performed; GPU execution and Windows/HIP operation were not qualified.

**Es wurde kein vollständiger Inferenztest durchgeführt.**

The public HF metadata contains no reference to this personal GitHub repository. Personal links were also removed from both README languages of the existing Flash-Next Overview, at revision `c038fc37a0f50c856c6c79a258aef422067c1ada`.

Earlier blocked/pre-release notes in the frozen source snapshot describe its state before deployment. This record supersedes them for build/release status; the code snapshot remains unchanged for reproducibility. The old CP2 scripts/workflows remain byte-for-byte unchanged.
