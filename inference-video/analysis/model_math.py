"""Back-of-envelope numbers for the video, computed from the models' configs.

    uv run python inference-video/analysis/model_math.py

Parameter counts per component, bytes read per decoded token, the decode
ceiling that implies at the M1 Max's 400 GB/s, and KV-cache sizes. Writes
model-math.json beside this script.
"""

import json
from pathlib import Path

MODELS = Path("/Volumes/ext1/lmstudio-models/lmstudio-community")
OUT = Path(__file__).parent / "model-math.json"
BANDWIDTH = 400e9  # bytes/s, M1 Max theoretical
BITS_4 = 4.5  # 4-bit weights + a 16-bit scale and offset per group of 64


def text_config(name):
    c = json.loads((MODELS / name / "config.json").read_text())
    return c.get("text_config", c)


def count(t):
    h, layers = t["hidden_size"], t["num_hidden_layers"]
    n_full = sum(x == "full_attention" for x in t["layer_types"])
    n_linear = layers - n_full

    # Gated attention: q (with output gate, so 2x), k, v, o
    q = t["num_attention_heads"] * t["head_dim"]
    kv = t["num_key_value_heads"] * t["head_dim"]
    full_attn = h * (2 * q + 2 * kv) + q * h
    # Gated DeltaNet: q, k, v, z (gate), b, a in; out
    qk = t["linear_num_key_heads"] * t["linear_key_head_dim"]
    v = t["linear_num_value_heads"] * t["linear_value_head_dim"]
    linear_attn = h * (2 * qk + 2 * v + 2 * t["linear_num_value_heads"]) + v * h
    attention = n_full * full_attn + n_linear * linear_attn

    vocab = t["vocab_size"] * h  # embedding table; the output head is the same size
    if "num_experts" in t:
        expert = 3 * h * t["moe_intermediate_size"]
        shared = 3 * h * t["shared_expert_intermediate_size"]
        ffn_total = layers * (t["num_experts"] * expert + shared + h * t["num_experts"])
        ffn_active = layers * (t["num_experts_per_tok"] * expert + shared + h * t["num_experts"])
        per_expert = expert
    else:
        ffn_total = ffn_active = layers * 3 * h * t["intermediate_size"]
        per_expert = None
    total = attention + ffn_total + 2 * vocab
    # per token: one embedding row (negligible), all attention, active FFN, the whole output head
    active = attention + ffn_active + vocab

    kv_per_token = n_full * 2 * kv * 2  # K and V, bf16
    # DeltaNet state per layer: one key_dim x value_dim matrix per value head, fp32
    state = n_linear * t["linear_num_value_heads"] * t["linear_key_head_dim"] * t["linear_value_head_dim"] * 4
    return {
        "layers": layers, "full_attention_layers": n_full, "linear_attention_layers": n_linear,
        "params_total_b": round(total / 1e9, 2), "params_active_b": round(active / 1e9, 2),
        "attention_b": round(attention / 1e9, 2), "ffn_total_b": round(ffn_total / 1e9, 2),
        "ffn_active_b": round(ffn_active / 1e9, 2), "output_head_b": round(vocab / 1e9, 2),
        "params_per_expert_m": per_expert and round(per_expert / 1e6, 2),
        "gb_read_per_token_4bit": round(active * BITS_4 / 8 / 1e9, 2),
        "decode_ceiling_4bit": round(BANDWIDTH / (active * BITS_4 / 8), 1),
        "gb_read_per_token_8bit": round(active * 8.5 / 8 / 1e9, 2),
        "decode_ceiling_8bit": round(BANDWIDTH / (active * 8.5 / 8), 1),
        "kv_bytes_per_token": kv_per_token,
        "kv_gb_at_262k": round(kv_per_token * 262144 / 1e9, 1),
        "kv_bytes_per_token_if_all_full_attention": layers * 2 * kv * 2,
        "deltanet_state_mb": round(state / 1e6, 1),
        "prefill_gflop_per_token": round(2 * active / 1e9, 1),
    }


def main():
    out = {
        "moe": count(text_config("Qwen3.6-35B-A3B-MLX-4bit")),
        "dense": count(text_config("Qwen3.6-27B-MLX-4bit")),
        # bench REPORT.md, 4-bit, 4,000-token prompt
        "measured": {"moe_decode": 67.3, "dense_decode": 18.5, "moe_prefill": 572, "dense_prefill": 89,
                     "moe_decode_8bit": 53.4, "dense_decode_8bit": 9.9},
    }
    m = out["measured"]
    for k in ("moe", "dense"):
        out[k]["decode_share_of_ceiling"] = round(m[f"{k}_decode"] / out[k]["decode_ceiling_4bit"], 2)
        out[k]["prefill_tflops"] = round(m[f"{k}_prefill"] * out[k]["prefill_gflop_per_token"] / 1e3, 2)
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
