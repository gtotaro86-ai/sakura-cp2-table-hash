# Sakura DeepSeek Engram cloud build

Dedicated source bundle and workflows for the DeepSeek Engram Q3_K build. Existing CP2 scripts and workflows are unchanged.

- DeepSeek Engram cloud checks: offline CPU/format/stream/HF-library checks, then read-only HF secret/identity preflight.
- Build and release DeepSeek Engram Q3_K: manual only; requires public no-cost HF storage confirmation and HF_TOKEN. Two table jobs, then original backbone server-copy and verified finalization.

Public model-card notice: **Es wurde kein vollständiger Inferenztest durchgeführt.**

No complete model has yet been released by adding these source files. See the source bundle's release/CLOUD_START.md for exact requirements.
