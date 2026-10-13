"""Pull one real group of 64 weights out of the 8-bit build, for the Bits scene.

    uv run python inference-video/analysis/weight_group.py

Reads a single tensor's bytes straight from the safetensors file (no model
load), dequantizes the first group of one expert's down-projection row, and
re-rounds it to 4 and 2 bits the way MLX's affine quantization does. Writes
weight-group.json beside this script.
"""

import json
import struct
from pathlib import Path

import numpy as np

MODEL = Path("/Volumes/ext1/lmstudio-models/lmstudio-community/Qwen3.6-35B-A3B-MLX-8bit")
PREFIX = "language_model.model.layers.20.mlp.switch_mlp.down_proj"
OUT = Path(__file__).parent / "weight-group.json"
GROUP = 64


def read_tensor(name):
    index = json.loads((MODEL / "model.safetensors.index.json").read_text())
    path = MODEL / index["weight_map"][name]
    with open(path, "rb") as f:
        header_len = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(header_len))
        meta = header[name]
        start, end = meta["data_offsets"]
        # just the first row's worth is plenty; read the first 64 KiB
        f.seek(8 + header_len + start)
        raw = f.read(min(end - start, 1 << 16))
    return meta, raw


def bf16(raw, n):
    u = np.frombuffer(raw[: 2 * n], dtype=np.uint16).astype(np.uint32) << 16
    return u.view(np.float32)


def requantize(w, bits):
    lo, hi = w.min(), w.max()
    scale = (hi - lo) / (2**bits - 1)
    q = np.round((w - lo) / scale)
    return (q * scale + lo).tolist(), q.astype(int).tolist(), float(lo), float(scale)


def main():
    meta, raw = read_tensor(f"{PREFIX}.weight")
    _, sraw = read_tensor(f"{PREFIX}.scales")
    _, braw = read_tensor(f"{PREFIX}.biases")
    assert meta["dtype"] == "U32", meta
    q8 = np.frombuffer(raw[:GROUP], dtype=np.uint8).astype(np.float32)  # 8-bit: one byte per weight
    scale, bias = bf16(sraw, 1)[0], bf16(braw, 1)[0]
    w = q8 * scale + bias
    out = {"tensor": PREFIX, "shape": meta["shape"], "weights": w.tolist(),
           "scale8": float(scale), "bias8": float(bias)}
    for bits in (4, 2):
        deq, q, lo, step = requantize(w, bits)
        out[f"q{bits}"] = {"levels": q, "dequantized": deq, "offset": lo, "step": step,
                           "rms_error": float(np.sqrt(np.mean((np.array(deq) - w) ** 2))),
                           "rms_weight": float(np.sqrt(np.mean(w ** 2)))}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "weights"}, indent=1)[:1500])


if __name__ == "__main__":
    main()
