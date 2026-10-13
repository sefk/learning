"""Measured numbers for the scenes, loaded from analysis/ (see its scripts)."""

import json
from pathlib import Path

_A = Path(__file__).parent / "analysis"


def _load(name):
    return json.loads((_A / name).read_text())


MATH = _load("model-math.json")
MEASURED = MATH["measured"]
ROUTING = _load("routing-summary.json")
ROUTING["sentence_routing_by_layer"] = ROUTING["keeper_routing"]
WEIGHTS = _load("weight-group.json")
QUANT = _load("quant-sweep.json")
