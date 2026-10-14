# Inside local inference — explainer video

An explainer in two parts, in the style of [3Blue1Brown][3b1b], on what
decides how fast and how well a model runs on your own machine: memory
bandwidth, mixture of experts, quantization, attention and the KV cache. It is
built around the Qwen models benchmarked in [`../../bench`][bench], and most
of its numbers are measured on the same Mac Studio (M1 Max, 64 GB) rather than
quoted.

| File | Part | Voice | Length |
|------|------|-------|--------|
| `local-inference-1.mp4` | 1. Mixture of experts | Heart | 12:39 |
| `local-inference-2.mp4` | 2. Quantization and context | Heart | 12:55 |

Heart (`af_heart`) is an American female voice from [Kokoro-82M][kokoro], run
locally. Every scene is a chapter in the mp4.

Narrated by Kokoro's Heart voice at 0.95× speed with longer pauses between
beats, for a slower pace than the thinking video. Built with the shared tools
in [`../kit`][kit]; see the [top-level README][top] for how.

## What it covers

Part 1: mixture of experts.

| Chapter | Scene | Idea |
|---------|-------|------|
| Two models, one Mac | `Hook` | The 35B mixture-of-experts model decodes 3.6× faster than the 27B dense one, at the same quality (MMLU and GSM8K, both explained). Why? |
| The memory wall | `MemoryWall` | Decode reads every active weight once per token: bandwidth ÷ bytes is a hard ceiling (27.8 tok/s for the dense model; 18.5 measured). Prefill is compute-bound instead. Two levers: fewer weights per token, fewer bits per weight. |
| Mixture of experts | `Experts` | The feed-forward network split into 256 experts per layer; a router picks 8, plus 1 shared; 320 routing decisions per token; 34.7 B stored, 2.95 B active. Load balancing. |
| What an expert actually is | `WhatExperts` | What experts actually do, from hooking the routers of the local 4-bit model (below). |
| Why 3.6× faster, not 9× | `MoESpeed` | Attention (1.28 B) is dense and bigger than the active experts; overhead dominates. The 4→8-bit slowdown (1.87× dense, 1.26× MoE) shows it. Prefill 6.4×. The catch: the dense model is the better coder. |
| Speculative decoding | `Speculative` | Verify several guessed tokens for the price of one read; draft models and Qwen's built-in multi-token-prediction layer; why it helps experts less. |
| Qwen 3 to 3.8 | `QwenLineage` | Qwen3-30B-A3B → Qwen3-Next → 3.5/3.6-35B-A3B: finer experts, a shared expert, 3:1 Gated DeltaNet. 3.6-27B and 3.8-27B configs are identical; 3.8 changed training (coding-agent benchmarks up, MMLU down on your benchmarks) and the lineup (512-expert MoEs, no 35B successor; Flash-Next's sparse attention and n-gram embeddings). Hand-off to part 2. |

Part 2: quantization and context.

| Chapter | Scene | Idea |
|---------|-------|------|
| Where part one left off | `PartTwo` | tokens/s ≈ bandwidth ÷ bytes per token; one lever done, two topics to go. |
| Quantization | `Bits` | Affine group quantization on 64 real weights from the model: 16 levels, offset + step per group, 4.5 bits per weight. Routers kept at 8-bit. Your benchmarks: 8-bit buys nothing. |
| Is 2-bit workable? | `TwoBits` | The requantization sweep (below). Smarter low-bit formats; binary and ternary (BitNet) need training that way. |
| Attention and heads | `Attention` | Query, key and value; scores, weights and the blend of values; heads, each with its own projections; grouped-query attention (16 query heads share 2 key/value heads); the KV cache, and why every token rereads it. |
| Gated DeltaNet | `DeltaNet` | A fixed 128 × 128 memory per head instead of a growing list: write key × value, read with a query; the delta rule writes only the correction; the gate fades or clears the memory. 63 MB at any length, but lossy, so 1 layer in 4 keeps full attention. |
| The KV cache | `KVCache` | 2 KB per attention layer per token; 20 KB per token (5.4 GB at 262k) vs ~96 KB for Qwen3-30B-A3B and 64 KB for the dense model; decode reads the cache too. |
| Reusing the cache | `Caching` | Prefix caching (11.6× on a repeated prompt, which the benchmarks had to defeat with a nonce); chat turns; why a DeltaNet state can't be rewound; API prompt caching; truncation, compaction, and silent failure when the window fills. |
| Recap | `Recap` | tokens/s ≈ bandwidth ÷ bytes per token, and what each lever costs. |

## Measurements made for this video

Everything in `analysis/` reruns from the models on `/Volumes/ext1`; the
JSON results are committed (except the raw router trace, which is 5 MB and
regenerates in under a minute).

- **`probe_router.py` → `analyze_routing.py`** — hooks all 40 routers of
  `Qwen3.6-35B-A3B-MLX-4bit` (via `mlx-lm`) and runs one forward pass over six
  text samples: Python, an English short story, math, Chinese, JSON and French
  prose (1,324 tokens). Findings:
  - Layer 0 experts sort by token *shape*: one takes 97% spaces, another 95%
    newlines, from every kind of text that has them.
  - At layer 20 the median busy expert gets 59% of its traffic from one
    sample (chance would be 17%), and 27 experts are ≥90% one sample — JSON,
    Python, Chinese and math each have their own. But English and French
    narration share 56% of their routing, English prose and Python only 12%:
    genre and syntax, not language or subject.
  - The router is diffuse: the top choice averages 4.3% of the probability,
    all eight winners 17%. Adjacent tokens share 3.0 of 8 experts (0.25 by
    chance).
  - One 191-token paragraph touches 5,007 of the 10,240 experts (49%), which
    is why all of them have to stay in memory.
- **`model_math.py`** — parameter counts per component, bytes per token,
  decode ceilings, and KV-cache sizes, computed from the two models'
  `config.json`. Totals come out at 34.7 B and 26.9 B, matching the names.
- **`weight_group.py`** — one real group of 64 weights read straight from the
  8-bit safetensors, re-rounded to 4 and 2 bits: typical error 9% and 46% of a
  weight's size.
- **`quant_sweep.py`** — starts from the 8-bit build, requantizes it in place
  (MLX affine, routers always kept at 8-bit), and scores each variant on the
  bench's 500 MMLU items by the A–D logit at the answer position (prefill
  only), plus perplexity on the six samples and a short completion. The
  published 4-bit build scores 83.8% this way, exactly what the bench's
  generate-and-parse grading measured, so the method agrees with it.

  | Variant | Bits/weight | GB | MMLU | Perplexity |
  |---|---|---|---|---|
  | 8-bit | 8.5 | 36.8 | 85.6% | 2.69 |
  | 4-bit | 4.5 | 19.5 | 85.0% | 2.76 |
  | 3-bit experts, 8-bit rest | 3.85 | 16.7 | 84.2% | 2.75 |
  | 3-bit | 3.5 | 15.2 | 75.4% | 3.22 |
  | 2-bit, groups of 32 | 3.0 | 13.0 | 34.4% | 8.43 |
  | 2-bit experts, 8-bit rest | 2.92 | 12.7 | **82.0%** | 3.14 |
  | 2-bit | 2.5 | 10.8 | 28.0% | 24.2 |

  Plain rounding falls off a cliff below 4 bits, but almost all of the 2-bit
  damage comes from the ~7% of weights outside the routed experts
  (attention, shared expert, embeddings, output head): crushing only the
  experts to 2 bits keeps 82% in less memory than uniform 3-bit. The
  groups-of-32 variant still writes a fluent paragraph about why the sky is
  blue while scoring 34%, so fluency is no test of a quant. Each variant takes
  about 5 minutes.

The sweep loads the 8-bit build (37 GB) and requantizes it in place, so on a
64 GB machine nothing else large should be running.

## Rebuilding

From the repo root:

```sh
uv run kit/tts_kokoro.py inference-video heart
uv run python -m kit.build inference-video heart --render
```

This writes both parts and prints each one's chapter timestamps.

The analysis scripts that need `mlx-lm` declare it inline, so each runs with
`uv run inference-video/analysis/<script>.py`; the rest use the project
environment (`uv run python …`).

## Sources

- Measurements: [`../../bench/REPORT.md`][report] and `analysis/` here.
- Model configs: the local MLX builds, and Hugging Face for
  [Qwen3-30B-A3B][q3], [Qwen3-Next-80B-A3B][qnext], [Qwen3.5-35B-A3B][q35],
  [Qwen3.8-2.4T-A95B][q38big] and [Qwen3.8-Flash-Next][q38flash].
- Qwen3.8-27B benchmark figures: its [model card][q38].
- [BitNet b1.58][bitnet].
- [Gated Delta Networks][gdn] (Yang, Kautz and Hatamizadeh, 2024) and
  [grouped-query attention][gqa] (Ainslie et al., 2023).

[3b1b]: https://www.3blue1brown.com/
[bench]: ../../bench/README.md
[report]: ../../bench/REPORT.md
[kokoro]: https://huggingface.co/hexgrad/Kokoro-82M
[kit]: ../kit/
[top]: ../README.md
[q3]: https://huggingface.co/Qwen/Qwen3-30B-A3B
[qnext]: https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct
[q35]: https://huggingface.co/Qwen/Qwen3.5-35B-A3B
[q38]: https://huggingface.co/Qwen/Qwen3.8-27B
[q38big]: https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B
[q38flash]: https://huggingface.co/Qwen/Qwen3.8-Flash-Next
[bitnet]: https://arxiv.org/abs/2402.17764
[gdn]: https://arxiv.org/abs/2412.06464
[gqa]: https://arxiv.org/abs/2305.13245
