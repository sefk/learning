# /// script
# requires-python = ">=3.12"
# dependencies = ["mlx-lm>=0.32"]
# ///
"""Record which experts Qwen3.6-35B-A3B's routers pick, token by token.

    uv run inference-video/analysis/probe_router.py [model-dir]

Runs one forward pass (prefill only) over a handful of text samples from
different domains, hooks every layer's router, and writes the top-8 choices
and their weights for every token at every layer to routing.json beside this
script. analyze_routing.py turns that into the numbers the video uses.
"""

import json
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load

MODEL = "/Volumes/ext1/lmstudio-models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"
OUT = Path(__file__).parent / "routing.json"

SAMPLES = {
    "code": '''def merge_intervals(intervals):
    """Merge overlapping [start, end] intervals."""
    if not intervals:
        return []
    intervals.sort(key=lambda pair: pair[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items = {}

    def get(self, key):
        if key not in self.items:
            return None
        value = self.items.pop(key)
        self.items[key] = value
        return value

    def put(self, key, value):
        self.items.pop(key, None)
        self.items[key] = value
        if len(self.items) > self.capacity:
            oldest = next(iter(self.items))
            del self.items[oldest]
''',
    "prose": """The lighthouse keeper had not spoken to another person in eleven days when
the supply boat finally rounded the point. She watched it from the gallery,
one hand on the cold iron rail, and tried to remember how conversation was
supposed to begin. The weather, probably. Everyone began with the weather.
The boat was smaller than she expected, painted a faded green, and the man at
the tiller wore a heavy wool coat that seemed far too warm for September. He
raised an arm in greeting. She raised one back, then felt foolish, because of
course he could not see her face from that distance, only a figure against the
white tower. By the time she reached the landing he had already tied off and
was handing up crates: flour, lamp oil, a sack of letters held together with
twine. "Wind's turning," he said, which was exactly what she had planned to say.""",
    "math": """Problem: A tank holds 240 liters. Pipe A fills it in 6 hours and pipe B fills
it in 8 hours, while a drain empties it in 12 hours. If all three are opened
when the tank is empty, how long until it is full?

Solution: Pipe A adds 240 / 6 = 40 liters per hour. Pipe B adds 240 / 8 = 30
liters per hour. The drain removes 240 / 12 = 20 liters per hour. The net rate
is 40 + 30 - 20 = 50 liters per hour. So the tank fills in 240 / 50 = 4.8 hours,
which is 4 hours and 48 minutes.

Check: in 4.8 hours, A adds 192 liters, B adds 144 liters, and the drain
removes 96 liters. 192 + 144 - 96 = 240. Correct.

Problem: Solve for x: 3(x - 4) + 2x = 5x - 12. Expanding gives 3x - 12 + 2x =
5x - 12, so 5x - 12 = 5x - 12, which holds for every x. The equation is an
identity and has infinitely many solutions.""",
    "chinese": """长江是中国最长的河流，全长约六千三百公里，发源于青藏高原的唐古拉山脉，
自西向东流经青海、西藏、四川、云南、重庆、湖北、湖南、江西、安徽、江苏和上海，
最后注入东海。长江流域面积广阔，气候温和，雨量充沛，自古以来就是中国重要的
农业区和经济带。沿江的城市如重庆、武汉、南京和上海，都因河运而兴盛。
三峡位于长江上游与中游的交界处，以山势险峻、江流湍急而闻名。二十世纪末开始
修建的三峡大坝，是世界上装机容量最大的水电站之一，既能发电，又能防洪和改善航运。
不过，大坝的建设也引起了关于移民、生态和文物保护的长期讨论。""",
    "json": """{
  "id": "ord_20481",
  "customer": {"name": "Ada Park", "email": "ada@example.com", "tier": "gold"},
  "items": [
    {"sku": "KB-104", "qty": 2, "unit_price": 49.5, "tags": ["keyboard", "wireless"]},
    {"sku": "MS-220", "qty": 1, "unit_price": 29.0, "tags": ["mouse"]},
    {"sku": "CB-007", "qty": 3, "unit_price": 7.25, "tags": ["cable", "usb-c"]}
  ],
  "shipping": {"method": "express", "cost": 12.0, "address": {"city": "Portland", "zip": "97205"}},
  "discount": {"code": "FALL10", "percent": 10},
  "status": "paid",
  "created_at": "2026-09-30T14:22:05Z",
  "notes": null
}""",
    "french": """La boulangerie ouvrait à six heures, mais la file d'attente commençait bien
avant. Les habitués se reconnaissaient sans se parler : un signe de tête, un
regard vers le ciel encore sombre. Madame Roux, qui tenait la caisse depuis
trente ans, connaissait les commandes de chacun par cœur. Une baguette bien
cuite pour le professeur, deux croissants pour la jeune infirmière qui rentrait
de garde, un pain de campagne pour le vieux monsieur au chien. Quand la porte
s'ouvrait enfin, l'odeur du pain chaud envahissait la rue, et pendant quelques
minutes, le quartier entier semblait se réveiller au même rythme.""",
}


class Recorder(nn.Module):
    """Wraps a router: passes its logits through and keeps a copy."""

    def __init__(self, gate):
        super().__init__()
        self.gate = gate
        self.logits = None

    def __call__(self, x):
        out = self.gate(x)
        self.logits = out
        return out


def main():
    model, tokenizer = load(sys.argv[1] if len(sys.argv) > 1 else MODEL)
    layers = model.language_model.model.layers
    recorders = []
    for layer in layers:
        rec = Recorder(layer.mlp.gate)
        layer.mlp.gate = rec
        recorders.append(rec)
    top_k = layers[0].mlp.top_k

    result = {"top_k": top_k, "num_experts": layers[0].mlp.num_experts, "samples": {}}
    for name, text in SAMPLES.items():
        ids = tokenizer.encode(text)
        model(mx.array([ids]))
        per_layer = []
        for rec in recorders:
            probs = mx.softmax(rec.logits[0].astype(mx.float32), axis=-1)
            inds = mx.argsort(-probs, axis=-1)[:, :top_k]
            weights = mx.take_along_axis(probs, inds, axis=-1)
            mx.eval(inds, weights)
            per_layer.append({"experts": inds.tolist(), "weights": [[round(w, 4) for w in row] for row in weights.tolist()]})
        result["samples"][name] = {
            "tokens": [tokenizer.decode([t]) for t in ids],
            "layers": per_layer,
        }
        print(f"{name}: {len(ids)} tokens", file=sys.stderr)
    OUT.write_text(json.dumps(result))
    print(OUT)


if __name__ == "__main__":
    main()
