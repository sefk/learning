# /// script
# requires-python = ">=3.12"
# dependencies = ["mlx-lm>=0.32"]
# ///
"""How much does each bit of precision buy on Qwen3.6-35B-A3B?

    uv run inference-video/analysis/quant_sweep.py [variant ...]

Starts from the 8-bit MLX build (the closest thing to full precision on this
machine), requantizes its weights to fewer bits in place, and measures each
variant on:

- MMLU: the 500 items from ../bench/quality/items.jsonl with the bench's own
  prompt, thinking off, scored by which of A/B/C/D gets the highest logit at
  the answer position (prefill only, so fast; not identical to the bench's
  generate-then-parse grading).
- Perplexity on the text samples in probe_router.py.
- A short greedy completion, to see what the numbers sound like.

Routers stay at 8 bits in every variant, as in the published MLX builds.
Requantizing from 8-bit stacks a little extra error on top, which is small
next to the 2- and 3-bit errors this is looking for. The actual 4-bit build
is also measured as a control. Results go to quant-sweep.json beside this
script, one entry per variant, merged with any earlier run.
"""

import json
import math
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
from mlx_lm.generate import generate
from mlx_lm.models.switch_layers import QuantizedSwitchLinear

sys.path.insert(0, str(Path(__file__).parent))
from probe_router import SAMPLES  # noqa: E402

MODELS = Path("/Volumes/ext1/lmstudio-models/lmstudio-community")
BASE = MODELS / "Qwen3.6-35B-A3B-MLX-8bit"
ITEMS = Path(__file__).resolve().parents[3] / "bench" / "quality" / "items.jsonl"
OUT = Path(__file__).parent / "quant-sweep.json"

MMLU_INSTRUCTIONS = (
    "Answer the multiple-choice question. Reply with a single letter (A, B, C, "
    "or D) and nothing else."
)
GEN_PROMPT = "In three sentences, explain why the sky is blue."

# name -> (bits for routed experts, bits for everything else, group size).
# None means "leave as stored".
VARIANTS = {
    "8-bit": (None, None, 64),
    "4-bit (published)": "load",
    "4-bit": (4, 4, 64),
    "3-bit": (3, 3, 64),
    "2-bit": (2, 2, 64),
    "2-bit experts, 8-bit rest": (2, None, 64),
    "3-bit experts, 8-bit rest": (3, None, 64),
    "2-bit, groups of 32": (2, 2, 32),
}


def requantize(model, expert_bits, other_bits, group_size):
    """Re-round every quantized weight (except routers) to fewer bits, in place.

    Returns (total weights, total bits) so the variant's size can be reported.
    """
    weights = bits_total = 0
    for path, module in model.named_modules():
        if not isinstance(module, (nn.QuantizedLinear, nn.QuantizedEmbedding, QuantizedSwitchLinear)):
            continue
        is_router = path.endswith("mlp.gate") or path.endswith("shared_expert_gate")
        is_expert = isinstance(module, QuantizedSwitchLinear)
        bits = None if is_router else (expert_bits if is_expert else other_bits)
        if bits is not None and (bits != module.bits or group_size != module.group_size):
            w = mx.dequantize(module.weight, module.scales, module.biases,
                              group_size=module.group_size, bits=module.bits)
            module.weight, module.scales, module.biases = mx.quantize(w, group_size=group_size, bits=bits)
            module.bits, module.group_size = bits, group_size
            mx.eval(module.weight, module.scales, module.biases)
            del w
        n = module.weight.size * 32 // module.bits
        weights += n
        # each group stores a 16-bit scale and a 16-bit offset alongside its weights
        bits_total += n * module.bits + (n // module.group_size) * 32
    return weights, bits_total


def mmlu(model, tokenizer):
    items = [json.loads(line) for line in ITEMS.read_text().splitlines()]
    items = [i for i in items if i["task"] == "mmlu"]
    letters = [tokenizer.encode(c)[0] for c in "ABCD"]
    correct = 0
    for item in items:
        choices = "\n".join(f"{l}. {t}" for l, t in zip("ABCD", item["choices"]))
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": f"{MMLU_INSTRUCTIONS}\n\n{item['question']}\n{choices}"}],
            add_generation_prompt=True, enable_thinking=False, tokenize=False,
        )
        logits = model(mx.array([tokenizer.encode(prompt)]))[0, -1]
        pick = "ABCD"[int(mx.argmax(logits[mx.array(letters)]))]
        correct += pick == item["answer"]
    return correct, len(items)


def perplexity(model, tokenizer):
    nll = count = 0
    for text in SAMPLES.values():
        ids = mx.array([tokenizer.encode(text)])
        logits = model(ids[:, :-1]).astype(mx.float32)
        losses = nn.losses.cross_entropy(logits, ids[:, 1:], reduction="sum")
        nll += float(losses)
        count += ids.shape[1] - 1
    return math.exp(nll / count)


def main():
    wanted = sys.argv[1:] or list(VARIANTS)
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name in wanted:
        spec = VARIANTS[name]
        t0 = time.time()
        if spec == "load":
            model, tokenizer = load(str(MODELS / "Qwen3.6-35B-A3B-MLX-4bit"))
            weights, bits = requantize(model, None, None, 64)
        else:
            model, tokenizer = load(str(BASE))
            weights, bits = requantize(model, *spec)
        right, total = mmlu(model, tokenizer)
        ppl = perplexity(model, tokenizer)
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": GEN_PROMPT}],
            add_generation_prompt=True, enable_thinking=False, tokenize=False,
        )
        sample = generate(model, tokenizer, prompt, max_tokens=90)
        results[name] = {
            "bits_per_weight": round(bits / weights, 2),
            "gb": round(bits / 8 / 1e9, 1),
            "mmlu_correct": right, "mmlu_total": total,
            "mmlu": round(right / total, 3),
            "perplexity": round(ppl, 3),
            "sample": sample,
            "seconds": round(time.time() - t0),
        }
        print(name, {k: v for k, v in results[name].items() if k != "sample"}, flush=True)
        print("   ", sample.replace("\n", " ")[:200], flush=True)
        OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False))
        del model
        mx.clear_cache()


if __name__ == "__main__":
    main()
