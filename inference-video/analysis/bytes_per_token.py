"""Bytes read per decoded token, measured from the weight files themselves.

    uv run python inference-video/analysis/bytes_per_token.py

Reads each safetensors header (no weights loaded) and sums the bytes a token
touches: every tensor except the embedding table (a lookup reads one row)
and the vision encoder (unused for text), with each layer's expert tensors
scaled by active/total experts. Compares the Qwen MoE with gpt-oss-20b, a
MoE built the other way: few, wide experts.
Writes bytes-per-token.json beside this script.
"""

import json
import re
import struct
from pathlib import Path

ROOT = Path("/Volumes/ext1/lmstudio-models")
OUT = Path(__file__).parent / "bytes-per-token.json"
BANDWIDTH = 400e9  # bytes/s, M1 Max theoretical
MODELS = {
    "qwen3.6-35b-a3b": ROOT / "lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit",
    "gpt-oss-20b": ROOT / "mlx-community/gpt-oss-20b-MXFP4-Q8",
}
EXPERT = re.compile(r"\.(experts|switch_mlp)\.")
SKIP = re.compile(r"embed_tokens|vision|visual")


def tensor_bytes(model_dir):
    sizes = {}
    for f in sorted(model_dir.glob("*.safetensors")):
        with open(f, "rb") as fh:
            n = struct.unpack("<Q", fh.read(8))[0]
            header = json.loads(fh.read(n))
        for name, meta in header.items():
            if name != "__metadata__":
                start, end = meta["data_offsets"]
                sizes[name] = end - start
    return sizes


def text_config(model_dir):
    c = json.loads((model_dir / "config.json").read_text())
    return c.get("text_config", c)


def summarize(model_dir):
    t = text_config(model_dir)
    experts = t.get("num_experts") or t["num_local_experts"]
    active = t["num_experts_per_tok"]
    total = per_token = 0
    for name, size in tensor_bytes(model_dir).items():
        total += size
        if SKIP.search(name):
            continue
        if EXPERT.search(name) and "shared" not in name:
            per_token += size * active / experts
        else:
            per_token += size
    return {
        "layers": t["num_hidden_layers"],
        "experts": experts,
        "active_experts": active,
        "expert_width": t.get("moe_intermediate_size") or t["intermediate_size"],
        "gb_on_disk": round(total / 1e9, 2),
        "gb_read_per_token": round(per_token / 1e9, 2),
        "decode_ceiling": round(BANDWIDTH / per_token, 1),
    }


if __name__ == "__main__":
    out = {name: summarize(d) for name, d in MODELS.items()}
    out["measured_decode"] = {"qwen3.6-35b-a3b": 67.3, "gpt-oss-20b": 85.6}  # ../bench, short prompt, 4-bit
    for name in MODELS:
        out[name]["share_of_ceiling"] = round(out["measured_decode"][name] / out[name]["decode_ceiling"], 2)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
