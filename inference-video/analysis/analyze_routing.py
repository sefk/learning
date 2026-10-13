"""Summarize routing.json into the numbers and examples the video uses.

    uv run python inference-video/analysis/analyze_routing.py

Writes routing-summary.json beside this script (committed; routing.json is
regenerable and git-ignored).
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def entropy_bits(counter):
    total = sum(counter.values())
    return -sum(c / total * math.log2(c / total) for c in counter.values() if c)


def main():
    data = json.loads((HERE / "routing.json").read_text())
    k, n_exp = data["top_k"], data["num_experts"]
    samples = data["samples"]
    domains = list(samples)
    n_layers = len(next(iter(samples.values()))["layers"])
    summary = {"top_k": k, "num_experts": n_exp, "layers": n_layers,
               "tokens": {d: len(s["tokens"]) for d, s in samples.items()}}

    # 1. How domain-specific is each expert? For each layer, an expert's share
    # of selections coming from its most frequent domain, normalised by token
    # counts (1/6 = no preference, 1 = only ever used by one domain).
    per_layer = []
    for layer in range(n_layers):
        use = defaultdict(Counter)  # expert -> domain -> rate (selections per token)
        picks = Counter()  # expert -> raw selection count
        for d in domains:
            rows = samples[d]["layers"][layer]["experts"]
            for row in rows:
                for e in row:
                    use[e][d] += 1 / len(rows)
                    picks[e] += 1
        used = [e for e in range(n_exp) if use[e]]
        # only experts picked often enough for a share to mean something
        busy = [e for e in used if picks[e] >= 20]
        purity = sorted(max(use[e].values()) / sum(use[e].values()) for e in busy)
        per_layer.append({
            "layer": layer,
            "experts_used": len(used),
            "experts_scored": len(busy),
            "median_purity": purity[len(purity) // 2],
            "experts_over_80pct_one_domain": sum(p > 0.8 for p in purity),
        })
    summary["per_layer"] = per_layer

    # 2. Overlap of expert usage between domains at a middle layer: share of
    # selections each pair of domains sends to the same experts.
    mid = n_layers // 2
    dist = {}
    for d in domains:
        c = Counter(e for row in samples[d]["layers"][mid]["experts"] for e in row)
        total = sum(c.values())
        dist[d] = {e: v / total for e, v in c.items()}
    summary["mid_layer"] = mid
    summary["overlap"] = {
        f"{a}|{b}": round(sum(min(dist[a].get(e, 0), dist[b].get(e, 0)) for e in range(n_exp)), 3)
        for i, a in enumerate(domains) for b in domains[i + 1:]
    }
    summary["experts_touched_per_domain_mid"] = {d: len(dist[d]) for d in domains}

    # 3. Adjacent tokens: how many of the 8 experts carry over to the next token?
    carry = []
    for d in domains:
        for layer in range(n_layers):
            rows = samples[d]["layers"][layer]["experts"]
            carry += [len(set(a) & set(b)) for a, b in zip(rows, rows[1:])]
    summary["adjacent_shared_mean"] = round(sum(carry) / len(carry), 2)
    summary["adjacent_shared_random"] = round(k * k / n_exp, 2)

    # 4. How peaked is the choice? Mean router probability on the top-1 and
    # on all top-k, and the selected experts' renormalised weights.
    top1, topk = [], []
    for d in domains:
        for layer in range(n_layers):
            for w in samples[d]["layers"][layer]["weights"]:
                top1.append(w[0])
                topk.append(sum(w))
    summary["router_prob_top1_mean"] = round(sum(top1) / len(top1), 3)
    summary["router_prob_topk_mean"] = round(sum(topk) / len(topk), 3)

    # 5. Distinct experts one sample touches across all layers, vs. total.
    summary["experts_touched_whole_sample"] = {
        d: sum(len({e for row in samples[d]["layers"][layer]["experts"] for e in row})
               for layer in range(n_layers))
        for d in domains
    }
    summary["experts_total"] = n_exp * n_layers

    # 6. Token-type experts: at each layer, experts whose selections are
    # concentrated on a small set of token strings, across domains.
    examples = []
    for layer in range(n_layers):
        hits = defaultdict(Counter)  # expert -> token string -> count
        doms = defaultdict(Counter)
        for d in domains:
            toks = samples[d]["tokens"]
            for tok, row in zip(toks, samples[d]["layers"][layer]["experts"]):
                for e in row:
                    hits[e][tok] += 1
                    doms[e][d] += 1
        for e, c in hits.items():
            total = sum(c.values())
            if total < 25:
                continue
            examples.append({
                "layer": layer, "expert": e, "count": total,
                "token_entropy_bits": round(entropy_bits(c), 2),
                "top_tokens": c.most_common(8),
                "domains": dict(doms[e].most_common()),
            })
    examples.sort(key=lambda x: x["token_entropy_bits"])
    summary["most_token_specific_experts"] = examples[:25]

    # 7. One sentence, one layer: the experts each token goes to.
    toks = samples["prose"]["tokens"][:14]
    summary["sentence_routing"] = {
        str(layer): [{"token": t, "experts": samples["prose"]["layers"][layer]["experts"][i],
                      "weights": samples["prose"]["layers"][layer]["weights"][i]}
                     for i, t in enumerate(toks)]
        for layer in (0, mid, n_layers - 1)
    }

    # 8. Overall load: per-expert selection counts at the mid layer, all domains.
    load = Counter(e for d in domains for row in samples[d]["layers"][mid]["experts"] for e in row)
    summary["mid_layer_load"] = [load.get(e, 0) for e in range(n_exp)]

    # 9. Heatmap data: selections per token, per domain, for the 48 busiest
    # experts at the first layer and the middle one.
    heat = {}
    for layer in (0, mid):
        rate = {d: Counter(e for row in samples[d]["layers"][layer]["experts"] for e in row) for d in domains}
        busiest = [e for e, _ in sum(rate.values(), Counter()).most_common(48)]
        heat[str(layer)] = {"experts": busiest, "rates": {
            d: [round(rate[d][e] / len(samples[d]["tokens"]), 3) for e in busiest] for d in domains}}
    summary["heatmap"] = heat

    # 10. Mid-layer experts that serve (almost) only one domain, with their tokens.
    exclusive = []
    for e in range(n_exp):
        per_dom = {d: [t for t, row in zip(samples[d]["tokens"], samples[d]["layers"][mid]["experts"]) if e in row]
                   for d in domains}
        total = sum(len(v) for v in per_dom.values())
        if total < 20:
            continue
        d, toks = max(per_dom.items(), key=lambda kv: len(kv[1]))
        if len(toks) / total >= 0.9:
            exclusive.append({"expert": e, "domain": d, "count": total, "tokens": toks[:24]})
    summary["mid_layer_exclusive"] = sorted(exclusive, key=lambda x: -x["count"])

    # 12. One token (" keeper" in the story) through every layer.
    idx = samples["prose"]["tokens"].index(" keeper")
    summary["keeper_routing"] = [samples["prose"]["layers"][layer]["experts"][idx] for layer in range(n_layers)]

    # 11. Every expert the prose sample touched, per layer (for the 40 x 256 grid).
    summary["prose_touched"] = [sorted({e for row in samples["prose"]["layers"][layer]["experts"] for e in row})
                                for layer in range(n_layers)]

    (HERE / "routing-summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("most_token_specific_experts", "sentence_routing", "mid_layer_load", "per_layer")},
                     indent=1, ensure_ascii=False))
    for row in per_layer[::4]:
        print(row)
    for ex in examples[:15]:
        print(ex["layer"], ex["expert"], ex["count"], ex["token_entropy_bits"], ex["top_tokens"][:5], list(ex["domains"])[:3])


if __name__ == "__main__":
    main()
