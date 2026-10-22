from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable, TYPE_CHECKING, cast

import numpy as np


# Engram hash constants from inference/engram.py, stored in the GGUF: the token map needs the HF tokenizers
# normalizers and the multipliers numpy's PCG64 stream, neither of which the runtime has.

def _is_prime(n: int) -> bool:
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, math.isqrt(n) + 1, 2))


def engram_primes(n_layers: int, max_ngram_size: int, n_heads: int, vocab_size: int) -> list[list[list[int]]]:
    """EngramLayout.from_args: [layer][ngram order 2..max][head] bucket moduli, never reused across layers."""
    seen: set[int] = set()
    out: list[list[list[int]]] = []
    for _ in range(n_layers):
        per_ngram = []
        for _ in range(max_ngram_size - 1):
            sizes, cur = [], vocab_size - 1
            for _ in range(n_heads):
                cand = cur + 1
                while not _is_prime(cand) or cand in seen:
                    cand += 1
                cur = cand
                seen.add(cur)
                sizes.append(cur)
            per_ngram.append(sizes)
        out.append(per_ngram)
    return out


def engram_multipliers(layer_ids: list[int], max_ngram_size: int, compressed_vocab_size: int) -> list[list[int]]:
    """compute_hash_multipliers: odd, bounded so that token_id * multiplier cannot overflow int64."""
    bound = max(1, (np.iinfo(np.int64).max // compressed_vocab_size) // 2)
    rows = []
    for layer_id in layer_ids:
        rng = np.random.default_rng(10007 * layer_id)
        values = rng.integers(low=0, high=bound, size=(max_ngram_size,), dtype=np.int64)
        rows.append([int(v) * 2 + 1 for v in values])
    return rows


