"""Full table SHA256 on a free public GitHub Actions runner.

No payload file is written. Refuses a full read outside GitHub Actions so the
user does not accidentally transfer 28.8 GB to their Windows PC.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

REPO = "unsloth/Qwen3.8-Flash-Next-GGUF"
REVISION = "766911a6b7369840a91dbcd95f9f997acaab6cd6"
FILE = "UD-IQ1_S/Qwen3.8-Flash-Next-UD-IQ1_S-00002-of-00003.gguf"
FILE_SIZE = 49990818368
TABLE_OFFSET = 364622656
TABLE_BYTES = 28800138240
REFERENCE = "dd55c28902f38cd88134b2a569c51282c5ffce30080487e1a645740115c56cc3"
CHUNK = 16 << 20


def read_range(start, end, size):
    url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{FILE}"
    last = None
    for attempt in range(8):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Range": f"bytes={start}-{end}",
                    "Accept-Encoding": "identity",
                    "User-Agent": "sakura-cp2-table-hash/1",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{FILE_SIZE}":
                    raise ValueError("Server did not honor the exact pinned table range")
                data = response.read(size + 1)
                if len(data) != size:
                    raise ValueError("Wrong response length")
                return data
        except Exception as exc:
            last = exc
            time.sleep(min(60, 2 ** attempt))
    raise last


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Full table read restricted to the remote GitHub Actions runner")
    if os.environ.get("GITHUB_REPOSITORY_VISIBILITY", "public") == "private":
        raise SystemExit("Private runner minutes are not used")
    digest = hashlib.sha256()
    done = 0
    started = time.time()
    while done < TABLE_BYTES:
        size = min(CHUNK, TABLE_BYTES - done)
        start = TABLE_OFFSET + done
        end = start + size - 1
        digest.update(read_range(start, end, size))
        done += size
        if done % (1 << 30) < size or done == TABLE_BYTES:
            print(json.dumps({
                "checked_bytes": done,
                "total_bytes": TABLE_BYTES,
                "elapsed_seconds": round(time.time() - started, 1),
            }), flush=True)
    value = digest.hexdigest()
    receipt = {
        "repo": REPO,
        "revision": REVISION,
        "filename": FILE,
        "table_offset": TABLE_OFFSET,
        "table_bytes": TABLE_BYTES,
        "table_sha256": value,
        "reference_table_sha256": REFERENCE,
        "full_payload_sha256_equal": value == REFERENCE,
        "payload_disk_bytes": 0,
        "method": "Full streaming SHA256 on a public GitHub-hosted runner; no payload file written",
    }
    print(json.dumps(receipt), flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf8") as handle:
            handle.write("```json\n" + json.dumps(receipt, indent=2) + "\n```\n")
    if value != REFERENCE:
        raise SystemExit("Table differs; do not reuse the old CP2 encoding as a conversion of this input")


if __name__ == "__main__":
    main()
