from kit.scene import *

from data import MATH, MEASURED, ROUTING
from scenes_a import bar

DOMAINS = ["code", "prose", "math", "chinese", "json", "french"]
DOMAIN_LABELS = {"code": "Python", "prose": "English story", "math": "math", "chinese": "Chinese",
                 "json": "JSON", "french": "French prose"}
DOMAIN_COLORS = {"code": C_GREEN, "prose": C_BLUE, "math": C_YELLOW, "chinese": C_RED, "json": C_PURPLE,
                 "french": C_TEAL}


def chip(text, color, size=24):
    label = T(text, size, color)
    box = SurroundingRectangle(label, buff=0.14, corner_radius=0.1, stroke_color=color, stroke_width=1.5,
                               fill_color=color, fill_opacity=0.1)
    return VGroup(box, label)


class WhatExperts(VScene):
    def construct(self):
        # Beat 0: the naive picture, then the experiment
        self.beat(0)
        naive = VGroup(*[chip(s, C_GREY, 26) for s in ("chemistry", "law", "poetry")]).arrange(RIGHT, buff=0.5)
        nl = T("a panel of specialists?", 30, C_GREY, slant=ITALIC).next_to(naive, UP, buff=0.4)
        g = VGroup(nl, naive).move_to(UP * 1.6)
        self.cue("The name suggests")
        self.play(FadeIn(nl), LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in naive], lag_ratio=0.3), run_time=1.5)
        self.cue("To find out")
        self.play(g.animate.set_opacity(0.3), run_time=0.6)
        probe = T("hooked the 40 routers of Qwen3.6-35B-A3B (4-bit, on this Mac)", 26).move_to(DOWN * 0.2)
        self.play(FadeIn(probe), run_time=0.8)
        self.cue("six kinds")
        chips = VGroup(*[chip(DOMAIN_LABELS[d], DOMAIN_COLORS[d], 24) for d in DOMAINS]).arrange(RIGHT, buff=0.25)
        chips.move_to(DOWN * 1.4)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in chips], lag_ratio=0.25), run_time=2.5)
        self.cue("Then I recorded")
        tokens = sum(ROUTING["tokens"].values())
        rec = T(f"{tokens:,} tokens × 40 layers × 8 choices = {tokens * 320:,} routing decisions", 24, C_GREY) \
            .move_to(DOWN * 2.6)
        self.play(FadeIn(rec), run_time=0.8)

        # Beat 1: layer 0 sorts by token shape
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("layer 0", 34, C_GREY).to_edge(UP, buff=0.5)
        self.play(FadeIn(title), run_time=0.5)
        by_id = {(x["layer"], x["expert"]): x for x in ROUTING["most_token_specific_experts"]}
        cards = VGroup()
        for key, what in (((0, 168), "a space"), ((0, 235), "a newline")):
            x = by_id[key]
            share = x["top_tokens"][0][1] / x["count"]
            head = M(f"expert {key[1]}", 28, C_GOLD)
            body = T(f"{share:.0%} of its {x['count']} picks: {what}", 26)
            doms = T("from: " + ", ".join(DOMAIN_LABELS[d] for d in x["domains"]), 22, C_GREY)
            cards.add(VGroup(head, body, doms).arrange(DOWN, buff=0.18))
        cards.arrange(DOWN, buff=0.8).move_to(DOWN * 0.3)
        self.cue("One expert takes")
        self.play(FadeIn(cards[0], shift=UP * 0.2), run_time=0.8)
        self.cue("Another takes")
        self.play(FadeIn(cards[1], shift=UP * 0.2), run_time=0.8)

        # Beat 2: layer 20 heatmap
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        heat = ROUTING["heatmap"]["20"]
        experts = heat["experts"]
        rates = heat["rates"]
        # order columns by the domain each expert leans toward most, so the blocks show
        lean = {e: max(DOMAINS, key=lambda d: rates[d][i]) for i, e in enumerate(experts)}
        order = sorted(range(len(experts)), key=lambda i: (DOMAINS.index(lean[experts[i]]),
                                                           -max(rates[d][i] for d in DOMAINS)))
        cell = 0.2
        grid = VGroup()
        for r, d in enumerate(DOMAINS):
            row = VGroup()
            for c, i in enumerate(order):
                col_max = max(rates[dd][i] for dd in DOMAINS) or 1
                v = rates[d][i] / col_max
                row.add(Rectangle(width=cell, height=0.42, stroke_width=0, fill_color=DOMAIN_COLORS[d],
                                  fill_opacity=0.08 + 0.9 * v ** 1.5))
            row.arrange(RIGHT, buff=0.03)
            grid.add(row)
        grid.arrange(DOWN, buff=0.06).move_to(RIGHT * 0.9 + UP * 0.5)
        labels = VGroup(*[T(DOMAIN_LABELS[d], 22, DOMAIN_COLORS[d]).next_to(grid[r], LEFT, buff=0.25)
                          for r, d in enumerate(DOMAINS)])
        title = T("layer 20: the 48 busiest experts (columns); brightness = share of that expert's use",
                  22, C_GREY).to_edge(UP, buff=0.5)
        self.play(FadeIn(title), FadeIn(labels), run_time=0.8)
        self.cue("Each row")
        self.play(LaggedStart(*[FadeIn(row, lag_ratio=0.02) for row in grid], lag_ratio=0.2), run_time=2.0)
        self.cue("Some are nearly exclusive")
        excl = {x["expert"]: x for x in ROUTING["mid_layer_exclusive"]}
        notes = VGroup()
        for d, example_count in (("json", 1), ("code", 1), ("chinese", 1)):
            pick = next(x for x in ROUTING["mid_layer_exclusive"] if x["domain"] == d and x["expert"] in experts)
            col = order.index(experts.index(pick["expert"]))
            cell_m = grid[DOMAINS.index(d)][col]
            toks = "".join(pick["tokens"][:14]).replace("\n", "⏎").strip()[:30]
            note = VGroup(M(f"expert {pick['expert']}: ", 22, DOMAIN_COLORS[d]), M(toks, 22, WHITE)) \
                .arrange(RIGHT, buff=0.05)
            notes.add(VGroup(SurroundingRectangle(cell_m, buff=0.03, color=WHITE, stroke_width=2), note))
        notes_text = VGroup(*[n[1] for n in notes]).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(DOWN * 2.4)
        for phrase, n in zip(["almost only inside JSON", "others only inside Python", "others only on Chinese"], notes):
            self.cue(phrase)
            self.play(Create(n[0]), FadeIn(n[1], shift=UP * 0.15), run_time=0.7)

        # Beat 3: what goes together
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("share of routing in common, layer 20", 26, C_GREY).to_edge(UP, buff=0.25)
        ov = ROUTING["overlap"]
        n = len(DOMAINS)
        mat = VGroup()
        size = 0.82
        for r in range(n):
            for c in range(n):
                a, b = DOMAINS[r], DOMAINS[c]
                v = 1.0 if a == b else ov.get(f"{a}|{b}", ov.get(f"{b}|{a}"))
                sq = Square(size, stroke_color=BG, stroke_width=2, fill_color=C_GOLD, fill_opacity=0.08 + 0.85 * v)
                sq.move_to([c * size, -r * size, 0])
                txt = T(f"{v:.0%}" if a != b else "", 20, WHITE if v < 0.6 else BG).move_to(sq)
                mat.add(VGroup(sq, txt))
        mat.move_to(RIGHT * 1.0 + DOWN * 0.75)
        rl = VGroup(*[T(DOMAIN_LABELS[d], 20, DOMAIN_COLORS[d]).next_to(mat[r * n][0], LEFT, buff=0.2)
                      for r, d in enumerate(DOMAINS)])
        cl = VGroup(*[T(DOMAIN_LABELS[d], 18, DOMAIN_COLORS[d]).rotate(PI / 4)
                      .next_to(mat[c][0], UP, buff=0.1) for c, d in enumerate(DOMAINS)])
        self.play(FadeIn(title), FadeIn(mat), FadeIn(rl), FadeIn(cl), run_time=1.2)
        p, f, c = DOMAINS.index("prose"), DOMAINS.index("french"), DOMAINS.index("code")
        self.cue("English and French")
        self.play(Indicate(mat[p * n + f], color=C_YELLOW, scale_factor=1.15),
                  Indicate(mat[f * n + p], color=C_YELLOW, scale_factor=1.15), run_time=1.2)
        self.cue("English narration and Python")
        self.play(Indicate(mat[p * n + c], color=C_YELLOW, scale_factor=1.15),
                  Indicate(mat[c * n + p], color=C_YELLOW, scale_factor=1.15), run_time=1.2)
        self.cue("The split is")
        verdict = T("genre and syntax, not language or subject", 28, C_YELLOW).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(verdict), run_time=0.8)

        # Beat 4: the router is rarely sure
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        tok = ROUTING["sentence_routing"]["20"][3]  # " keeper" at layer 20
        ws = tok["weights"]
        title = T(f"router probabilities for “{tok['token'].strip()}” at layer 20 (top 8 of 256)", 24, C_GREY) \
            .to_edge(UP, buff=0.5)
        bars = VGroup(*[Rectangle(width=0.5, height=max(0.03, 70 * w), stroke_width=0, fill_color=C_GOLD,
                                  fill_opacity=0.85) for w in ws]).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        bars.move_to(LEFT * 2.8 + DOWN * 0.2)
        vals = VGroup(*[T(f"{w:.1%}", 16, C_GREY).next_to(b, UP, buff=0.08) for b, w in zip(bars, ws)])
        self.play(FadeIn(title), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.1),
                  FadeIn(vals), run_time=1.5)
        self.cue("Its top choice")
        s1 = T(f"top choice, on average: {ROUTING['router_prob_top1_mean']:.1%}", 28).move_to(RIGHT * 3.3 + UP * 1.0)
        self.play(FadeIn(s1), run_time=0.6)
        self.cue("All eight winners")
        s2 = T(f"all eight together: {ROUTING['router_prob_topk_mean']:.0%}", 28).next_to(s1, DOWN, buff=0.3)
        self.play(FadeIn(s2), run_time=0.6)
        self.cue("Neighbouring tokens")
        s3 = T(f"next token reuses {ROUTING['adjacent_shared_mean']:.1f} of 8", 28, C_YELLOW).next_to(s2, DOWN, buff=0.5)
        s4 = T(f"(by chance: {ROUTING['adjacent_shared_random']:.2f})", 22, C_GREY).next_to(s3, DOWN, buff=0.15)
        self.play(FadeIn(s3), FadeIn(s4), run_time=0.8)

        # Beat 5: half of all experts in one paragraph
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        touched = ROUTING["prose_touched"]
        rows = VGroup()
        for layer in range(40):
            row = VGroup(*[Rectangle(width=0.042, height=0.1, stroke_width=0, fill_color=C_DIM, fill_opacity=0.5)
                           for _ in range(256)]).arrange(RIGHT, buff=0.006)
            rows.add(row)
        rows.arrange(DOWN, buff=0.03).move_to(DOWN * 0.1)
        cap = T("all 10,240 experts (40 layers × 256)", 22, C_GREY).next_to(rows, UP, buff=0.2)
        self.play(FadeIn(rows), FadeIn(cap), run_time=0.8)
        self.cue("touches about half")
        lit = [rows[layer][e] for layer in range(40) for e in touched[layer]]
        self.play(LaggedStart(*[c.animate.set_fill(C_BLUE, opacity=1.0) for c in lit], lag_ratio=0.0004),
                  run_time=2.5)
        n_lit = ROUTING["experts_touched_whole_sample"]["prose"]
        res = T(f"one {ROUTING['tokens']['prose']}-token paragraph: {n_lit:,} experts ({n_lit / 10240:.0%})", 26,
                C_BLUE).next_to(rows, DOWN, buff=0.25)
        self.play(FadeIn(res), run_time=0.6)
        self.cue("so all thirty-five")
        mem = T("all 35 B parameters stay in memory", 30, C_YELLOW).move_to(cap)
        self.play(FadeOut(cap), FadeIn(mem), run_time=0.8)

        # Beat 6: summary
        self.beat(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        lines = VGroup(
            T("an expert = a learned slice of the feed-forward network", 32),
            T("specialised by form (syntax, genre), not by subject", 32),
            T("saves compute and bandwidth, not memory", 32, C_YELLOW),
        ).arrange(DOWN, buff=0.5)
        for phrase, line in zip(["So an expert", "Its specialisation", "Mixture of experts saves"], lines):
            self.cue(phrase)
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.7)
        self.end()


class MoESpeed(VScene):
    def construct(self):
        moe, dense = MATH["moe"], MATH["dense"]

        # Beat 0: the ceiling vs the measurement
        self.beat(0)
        eq = VGroup(T(f"{moe['params_active_b']:.2f} B active", 30), T("×", 30, C_GREY), T("4.5 bits", 30),
                    T("=", 30, C_GREY), T(f"{moe['gb_read_per_token_4bit']:.2f} GB per token", 30, C_YELLOW)) \
            .arrange(RIGHT, buff=0.25).to_edge(UP, buff=0.7)
        self.play(Write(eq), run_time=1.5)
        self.cue("That predicts")
        ceil = moe["decode_ceiling_4bit"]
        b1 = bar(ceil, ceil, 9, C_DIM).move_to(UP * 0.6).align_to(LEFT * 4.3, LEFT)
        l1 = T(f"ceiling {ceil:.0f} tokens/s", 24, C_GREY).next_to(b1, UP, buff=0.1).align_to(b1, LEFT)
        self.play(GrowFromEdge(b1, LEFT), FadeIn(l1), run_time=0.8)
        self.cue("The measurement")
        b2 = bar(MEASURED["moe_decode"], ceil, 9, C_GOLD).move_to(DOWN * 0.6).align_to(LEFT * 4.3, LEFT)
        l2 = T(f"measured {MEASURED['moe_decode']} tokens/s ({moe['decode_share_of_ceiling']:.0%})", 24, C_GOLD) \
            .next_to(b2, UP, buff=0.1).align_to(b2, LEFT)
        self.play(GrowFromEdge(b2, LEFT), FadeIn(l2), run_time=0.8)
        self.cue("Where did")
        q = T("where did the rest go?", 30, C_YELLOW).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(q), run_time=0.6)

        # Beat 1: what one token reads
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("parameters one token reads, Qwen3.6-35B-A3B", 26, C_GREY).to_edge(UP, buff=0.6)
        parts = [("attention (dense: every token)", moe["attention_b"], C_TEAL),
                 ("8 routed + 1 shared expert, routers", moe["ffn_active_b"], C_GOLD),
                 ("output layer (248k vocabulary)", moe["output_head_b"], C_GREY)]
        rows = VGroup()
        for i, (name, v, c) in enumerate(parts):
            b = bar(v, 1.4, 7, c).move_to([0, 1.0 - i * 1.1, 0]).align_to(LEFT * 3.5, LEFT)
            lab = T(f"{name}: {v:.2f} B", 24, c).next_to(b, UP, buff=0.08).align_to(b, LEFT)
            rows.add(VGroup(b, lab))
        self.play(FadeIn(title), run_time=0.5)
        self.cue("attention isn't sparse")
        self.play(GrowFromEdge(rows[0][0], LEFT), FadeIn(rows[0][1]), run_time=0.8)
        self.cue("That's more than")
        self.play(GrowFromEdge(rows[1][0], LEFT), FadeIn(rows[1][1]), run_time=0.8)
        self.cue("Then there's")
        self.play(GrowFromEdge(rows[2][0], LEFT), FadeIn(rows[2][1]), run_time=0.8)

        # Beat 2: overhead
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        steps = ["route", "gather 8", "9 small MLPs", "blend"]
        chain = VGroup(*[chip(s, C_GOLD, 24) for s in steps]).arrange(RIGHT, buff=0.5)
        arrows = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.08, color=C_GREY)
                          for i in range(3)])
        x40 = T("× 40 layers, every token", 28, C_GREY)
        g = VGroup(VGroup(chain, arrows), x40).arrange(DOWN, buff=0.4).move_to(UP * 1.0)
        self.cue("Forty layers")
        self.play(LaggedStart(*[FadeIn(c) for c in chain], lag_ratio=0.3), FadeIn(arrows), run_time=1.5)
        self.play(FadeIn(x40), run_time=0.5)
        self.cue("Small operations")
        tl = T("where decode time goes (schematic)", 22, C_GREY).move_to(DOWN * 0.9)
        busy = VGroup(*[Rectangle(width=w, height=0.45, stroke_width=0, fill_color=c, fill_opacity=0.85)
                        for w, c in [(0.5, C_YELLOW), (0.9, C_DIM), (0.4, C_YELLOW), (1.1, C_DIM), (0.6, C_YELLOW),
                                     (0.8, C_DIM), (0.5, C_YELLOW), (1.0, C_DIM), (0.45, C_YELLOW), (0.9, C_DIM)]]) \
            .arrange(RIGHT, buff=0).next_to(tl, DOWN, buff=0.25)
        key = VGroup(chip("moving bytes", C_YELLOW, 20), chip("bookkeeping, launching small kernels", C_GREY, 20)) \
            .arrange(RIGHT, buff=0.4).next_to(busy, DOWN, buff=0.3)
        self.play(FadeIn(tl), LaggedStart(*[GrowFromEdge(b, LEFT) for b in busy], lag_ratio=0.1), FadeIn(key),
                  run_time=1.8)

        # Beat 3: 8-bit slowdown tells the story
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("decode slowdown from 4-bit to 8-bit (twice the bytes)", 26, C_GREY).to_edge(UP, buff=0.6)
        ax_len = 8
        ref = DashedLine(ORIGIN, UP * 3.2, color=C_GREY).move_to(LEFT * 3.5 + RIGHT * ax_len * 2 / 2.2 + DOWN * 0.4)
        refl = T("2× = purely bandwidth-bound", 20, C_GREY).next_to(ref, UP, buff=0.1)
        d_r = MEASURED["dense_decode"] / MEASURED["dense_decode_8bit"]
        m_r = MEASURED["moe_decode"] / MEASURED["moe_decode_8bit"]
        bd = bar(d_r, 2.2, ax_len, C_BLUE, height=0.7).move_to(UP * 0.4).align_to(LEFT * 3.5, LEFT)
        bm = bar(m_r, 2.2, ax_len, C_GOLD, height=0.7).move_to(DOWN * 1.0).align_to(LEFT * 3.5, LEFT)
        ld = T("dense", 26, C_BLUE).next_to(bd, LEFT, buff=0.2)
        lm = T("experts", 26, C_GOLD).next_to(bm, LEFT, buff=0.2)
        vd = T(f"{d_r:.2f}×", 28, BG).move_to(bd.get_right(), aligned_edge=RIGHT).shift(LEFT * 0.15)
        vm = T(f"{m_r:.2f}×", 28, BG).move_to(bm.get_right(), aligned_edge=RIGHT).shift(LEFT * 0.15)
        self.play(FadeIn(title), Create(ref), FadeIn(refl), run_time=0.8)
        self.cue("makes the dense model")
        self.play(GrowFromEdge(bd, LEFT), FadeIn(ld), FadeIn(vd), run_time=0.8)
        self.cue("The mixture of experts only")
        self.play(GrowFromEdge(bm, LEFT), FadeIn(lm), FadeIn(vm), run_time=0.8)

        # Beat 4: prefill
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("time to first token, 4,000-token prompt", 26, C_GREY).to_edge(UP, buff=0.6)
        td = bar(36.6, 40, 10, C_BLUE, height=0.7).move_to(UP * 0.4).align_to(LEFT * 5, LEFT)
        tm = bar(5.7, 40, 10, C_GOLD, height=0.7).move_to(DOWN * 0.9).align_to(LEFT * 5, LEFT)
        ltd = T("dense 36.6 s", 26, C_BLUE).next_to(td, UP, buff=0.1).align_to(td, LEFT)
        ltm = T("experts 5.7 s", 26, C_GOLD).next_to(tm, UP, buff=0.1).align_to(tm, LEFT)
        pf = T(f"prefill: {MEASURED['moe_prefill']} vs {MEASURED['dense_prefill']} tokens/s "
               f"({MEASURED['moe_prefill'] / MEASURED['dense_prefill']:.1f}×)", 26).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(title), FadeIn(pf), run_time=0.6)
        self.cue("That's why")
        self.play(GrowFromEdge(td, LEFT), FadeIn(ltd), GrowFromEdge(tm, LEFT), FadeIn(ltm), run_time=1.5)

        # Beat 5: the catch, on code
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = VGroup(T("LiveCodeBench: 175 recent coding-contest problems", 26, C_GREY),
                       T("16k-token budget · your benchmarks", 22, C_GREY)).arrange(DOWN, buff=0.1) \
            .to_edge(UP, buff=0.5)
        self.play(FadeIn(title), run_time=0.5)
        self.cue("the dense model solved")
        cd = bar(60.6, 70, 8, C_BLUE, height=0.6).move_to(UP * 1.0).align_to(LEFT * 4, LEFT)
        cm = bar(50.9, 70, 8, C_GOLD, height=0.6).move_to(DOWN * 0.1).align_to(LEFT * 4, LEFT)
        lcd = T("dense 60.6%", 24, C_BLUE).next_to(cd, RIGHT, buff=0.2)
        lcm = T("experts 50.9%", 24, C_GOLD).next_to(cm, RIGHT, buff=0.2)
        self.play(GrowFromEdge(cd, LEFT), FadeIn(lcd), GrowFromEdge(cm, LEFT), FadeIn(lcm), run_time=1.0)
        self.cue("Head to head")
        wins = VGroup(*[Dot(radius=0.09, color=C_BLUE) for _ in range(27)]).arrange(RIGHT, buff=0.06)
        losses = VGroup(*[Dot(radius=0.09, color=C_GOLD) for _ in range(10)]).arrange(RIGHT, buff=0.06)
        hh = VGroup(VGroup(T("only dense solved: 27", 22, C_BLUE), wins).arrange(RIGHT, buff=0.3),
                    VGroup(T("only experts solved: 10", 22, C_GOLD), losses).arrange(RIGHT, buff=0.3)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(DOWN * 1.8)
        p = T("p = 0.008", 22, C_GREY).next_to(hh, DOWN, buff=0.2)
        self.play(FadeIn(hh[0][0]), LaggedStart(*[FadeIn(d) for d in wins], lag_ratio=0.05), run_time=1.2)
        self.play(FadeIn(hh[1][0]), LaggedStart(*[FadeIn(d) for d in losses], lag_ratio=0.05), FadeIn(p),
                  run_time=1.0)
        self.end()


def qwen_row(name, date, facts, color):
    head = VGroup(M(name, 24, color), T(date, 20, C_GREY)).arrange(RIGHT, buff=0.3)
    body = T(facts, 22)
    return VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.1)


def speed_formula():
    return VGroup(T("tokens/s", 36), T("≈", 36, C_GREY), T("bandwidth", 36, C_BLUE), T("÷", 36, C_GREY),
                  T("bytes per token", 36, C_YELLOW)).arrange(RIGHT, buff=0.25).to_edge(UP, buff=0.8)


def lever_list():
    """Part one's lever (done) and part two's two topics, for the hand-off between parts."""
    levers = VGroup(
        VGroup(T("✓", 30, C_GREEN), T("touch fewer weights per token: mixture of experts", 30, C_GOLD)),
        VGroup(T("→", 30, C_GREY), T("make each weight smaller: quantization", 30, C_PURPLE)),
        VGroup(T("→", 30, C_GREY), T("the memory that grows as you talk: context", 30, C_BLUE)),
    )
    for r in levers:
        r.arrange(RIGHT, buff=0.3)
    return levers.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to(DOWN * 0.3)


def layer_pattern(kinds, w=0.22, h=0.45):
    return VGroup(*[Rectangle(width=w, height=h, stroke_width=0,
                              fill_color=C_TEAL if k == "A" else C_PURPLE, fill_opacity=0.85)
                    for k in kinds]).arrange(RIGHT, buff=0.04)


class QwenLineage(VScene):
    def construct(self):
        # Beat 0: Qwen3-30B-A3B
        self.beat(0)
        title = T("Qwen mixture-of-experts models, from the published configs", 26, C_GREY).to_edge(UP, buff=0.4)
        r0 = qwen_row("Qwen3-30B-A3B", "Apr 2025", "128 experts, 8 active · full attention in all 48 layers", C_GREY)
        r0.move_to(UP * 2.0).to_edge(LEFT, buff=1.0)
        self.play(FadeIn(title), run_time=0.6)
        self.cue("Qwen three, in spring")
        self.play(FadeIn(r0, shift=RIGHT * 0.2), run_time=0.8)
        p0 = layer_pattern("A" * 48, w=0.12).next_to(r0, DOWN, buff=0.15).align_to(r0, LEFT)
        self.play(FadeIn(p0, lag_ratio=0.02), run_time=0.8)

        # Beat 1: Qwen3-Next, 3.5, 3.6
        self.beat(1)
        r1 = qwen_row("Qwen3-Next-80B-A3B", "Sep 2025", "512 experts, 10 + 1 shared · 3 of 4 layers Gated DeltaNet",
                      C_PURPLE).next_to(p0, DOWN, buff=0.45).align_to(r0, LEFT)
        self.cue("Then came")
        self.play(FadeIn(r1, shift=RIGHT * 0.2), run_time=0.8)
        r2 = qwen_row("Qwen3.5 / 3.6-35B-A3B", "2026", "256 experts, 8 + 1 shared · 30 DeltaNet + 10 attention layers",
                      C_GOLD).next_to(r1, DOWN, buff=0.45).align_to(r0, LEFT)
        self.cue("Experts got smaller")
        self.play(FadeIn(r2, shift=RIGHT * 0.2), run_time=0.8)
        self.cue("three out of every four")
        p2 = layer_pattern("DDDA" * 10, w=0.12).next_to(r2, DOWN, buff=0.15).align_to(r0, LEFT)
        key = VGroup(chip("full attention", C_TEAL, 18), chip("Gated DeltaNet", C_PURPLE, 18)) \
            .arrange(RIGHT, buff=0.3).next_to(p2, RIGHT, buff=0.5)
        self.play(FadeIn(p2, lag_ratio=0.02), FadeIn(key), run_time=1.2)
        self.cue("Qwen three point six thirty-five B is the same")
        same = T("3.6 = 3.5's architecture, new weights", 24, C_YELLOW).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(same), run_time=0.6)

        # Beat 2: 3.6 vs 3.8 27B configs are identical
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        fields = [("layers", "64"), ("hidden size", "5,120"), ("feed-forward width", "17,408"),
                  ("attention layers", "every 4th"), ("KV heads × dim", "4 × 256"),
                  ("DeltaNet heads", "16 qk, 48 v"), ("context", "262,144"), ("vocabulary", "248,320")]
        head = VGroup(T("", 24), M("Qwen3.6-27B", 24, C_BLUE), M("Qwen3.8-27B", 24, C_GREEN))
        rows = VGroup(head, *[VGroup(T(f, 24, C_GREY), M(v, 22), M(v, 22)) for f, v in fields])
        for row in rows:
            for j, cell in enumerate(row):
                cell.move_to([-3.8 + j * 3.6, 0, 0])
        rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT, center=False)
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                cell.move_to([-3.8 + j * 3.6, 2.6 - i * 0.55, 0])
        self.play(FadeIn(head), run_time=0.5)
        self.cue("The configuration files")
        self.play(LaggedStart(*[FadeIn(r) for r in rows[1:]], lag_ratio=0.15), run_time=2.0)
        self.cue("Same layers")
        eqs = VGroup(*[T("=", 26, C_YELLOW).move_to([1.6, r.get_y(), 0]) for r in rows[1:]])
        self.play(LaggedStart(*[FadeIn(e) for e in eqs], lag_ratio=0.1), run_time=1.0)
        self.cue("Different weights")
        dw = T("identical architecture · different weights", 28, C_YELLOW).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(dw), run_time=0.6)

        # Beat 3: what the training targeted
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("27B, Qwen3.6 → Qwen3.8", 28, C_GREY).to_edge(UP, buff=0.5)
        rows = [("SWE-bench Pro", 53.5, 61.7, "fix real issues in real repos · Qwen model card"),
                ("Terminal Bench 2.1", 63.4, 73.0, "agent work at a command line · Qwen model card"),
                ("MMLU, 4-bit", 86.2, 78.8, "57-subject exam · your benchmarks")]
        group = VGroup()
        for i, (name, a, b, src) in enumerate(rows):
            y = 1.4 - i * 1.4
            ba = bar(a, 100, 5.6, C_BLUE, height=0.32).move_to([0, y + 0.2, 0]).align_to(ORIGIN, LEFT)
            bb = bar(b, 100, 5.6, C_GREEN, height=0.32).move_to([0, y - 0.2, 0]).align_to(ORIGIN, LEFT)
            la = T(f"{a}", 20, C_BLUE).next_to(ba, RIGHT, buff=0.15)
            lb = T(f"{b}", 20, C_GREEN).next_to(bb, RIGHT, buff=0.15)
            name_l = VGroup(T(name, 24), T(src, 18, C_GREY)).arrange(DOWN, aligned_edge=RIGHT, buff=0.05) \
                .next_to(VGroup(ba, bb), LEFT, buff=0.4)
            group.add(VGroup(ba, bb, la, lb, name_l))
        key = VGroup(chip("3.6", C_BLUE, 20), chip("3.8", C_GREEN, 20)).arrange(RIGHT, buff=0.3) \
            .to_edge(DOWN, buff=0.4)
        self.play(FadeIn(title), FadeIn(key), run_time=0.5)
        for phrase, g in zip(["SWE-bench Pro", "Terminal Bench", "benchmarks measured"], group):
            self.cue(phrase)
            self.play(FadeIn(g[4]), GrowFromEdge(g[0], LEFT), GrowFromEdge(g[1], LEFT), FadeIn(g[2]), FadeIn(g[3]),
                      run_time=0.9)

        # Beat 4: the 3.8 lineup, one row per model on a log axis of parameters
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("Qwen open-weight models: parameters, log scale", 26, C_GREY).to_edge(UP, buff=0.4)
        x0, per_decade = -2.0, 1.9

        def x(b):  # billions of parameters -> x position
            return x0 + np.log10(b) * per_decade

        axis = Line([x0, -2.1, 0], [x(3000), -2.1, 0], color=C_GREY, stroke_width=2)
        ticks = VGroup(*[VGroup(Line([x(v), -2.1, 0], [x(v), -2.2, 0], color=C_GREY),
                                T(lab, 20, C_GREY).move_to([x(v), -2.45, 0]))
                         for v, lab in ((1, "1 B"), (10, "10 B"), (100, "100 B"), (1000, "1 T"))])
        key = VGroup(chip("total parameters", C_DIM, 18), chip("active per token", C_YELLOW, 18)) \
            .arrange(RIGHT, buff=0.3).next_to(title, DOWN, buff=0.25)
        models = [("3.6-27B", 27, 27, C_BLUE), ("3.6-35B-A3B", 35, 3, C_GOLD), ("3.8-27B", 27, 27, C_GREEN),
                  ("3.8-Flash-Next", 180, 6, C_GREEN), ("3.8-2.4T-A95B", 2400, 95, C_GREEN)]
        rows = VGroup()
        for i, (name, total, active, c) in enumerate(models):
            y = 1.5 - i * 0.72
            whole = Rectangle(width=x(total) - x0, height=0.36, stroke_width=0, fill_color=c, fill_opacity=0.3) \
                .move_to([x0, y, 0], aligned_edge=LEFT)
            act = Rectangle(width=x(active) - x0, height=0.36, stroke_width=0, fill_color=c, fill_opacity=0.95) \
                .move_to([x0, y, 0], aligned_edge=LEFT)
            label = M(name, 22, c).next_to(whole, LEFT, buff=0.25)
            nums = f"{total:,} B" if total == active else f"{total:,} B, {active} B active"
            if name == "3.8-Flash-Next":
                nums = "~180 B, 6 B active"
            val = T(nums, 20, c).next_to(whole, RIGHT, buff=0.15)
            rows.add(VGroup(whole, act, label, val))
        limit = x(64 / 0.5625)  # 4.5 bits per weight
        moe_y = rows[1].get_y()  # leave a gap where the 35B row's label crosses the line
        mem = VGroup(DashedLine([limit, -2.1, 0], [limit, moe_y - 0.22, 0], color=C_RED),
                     DashedLine([limit, moe_y + 0.22, 0], [limit, 1.95, 0], color=C_RED))
        meml = T("← fits in 64 GB at 4-bit", 20, C_RED).next_to(mem.get_top(), RIGHT, buff=0.1)
        self.play(FadeIn(title), FadeIn(key), Create(axis), FadeIn(ticks), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(r) for r in rows[:3]], lag_ratio=0.3), run_time=1.2)
        self.cue("The open mixture models jumped")
        self.play(LaggedStart(*[FadeIn(r) for r in rows[3:]], lag_ratio=0.3), run_time=1.0)
        spec = T("both: 512 experts, 10 active + 1 shared", 22, C_GREEN).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(spec), run_time=0.6)
        self.cue("Neither fits")
        self.play(Create(mem), FadeIn(meml), run_time=0.8)

        # Beat 5: Flash previews sparse attention and n-gram embeddings
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("Qwen3.8-Flash-Next: what changes next", 28, C_GREY).to_edge(UP, buff=0.5)
        self.play(FadeIn(title), run_time=0.5)
        self.cue("Full attention is replaced")
        past = VGroup(*[Square(0.22, stroke_width=0, fill_color=C_DIM, fill_opacity=0.7) for _ in range(40)]) \
            .arrange(RIGHT, buff=0.05).move_to(UP * 1.2)
        now = token_box("now", C_YELLOW, 20).next_to(past, RIGHT, buff=0.3)
        self.play(FadeIn(past), FadeIn(now), run_time=0.6)
        self.cue("a small indexer")
        pick = [3, 4, 5, 6, 17, 18, 19, 20, 31, 32, 33, 34]
        idx = T("indexer picks which blocks to attend to", 22, C_TEAL).next_to(past, DOWN, buff=0.3)
        self.play(*[past[i].animate.set_fill(C_TEAL, opacity=1) for i in pick], FadeIn(idx), run_time=1.0)
        self.cue("And it adds")
        table = VGroup(*[VGroup(M(k, 20, C_GOLD), T("→ vector", 20, C_GREY)).arrange(RIGHT, buff=0.2)
                         for k in ("“of the”", "“in order to”", "“def __init__”", "…")]) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(DOWN * 1.6 + LEFT * 2.5)
        tl = T("n-gram embeddings: 51 B parameters of lookup tables", 22, C_GOLD).next_to(table, UP, buff=0.25)
        self.play(FadeIn(tl), FadeIn(table, lag_ratio=0.2), run_time=1.2)
        self.cue("Like experts")
        cost = VGroup(T("memory: lots", 26, C_RED), T("compute: almost none", 26, C_GREEN)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(DOWN * 1.6 + RIGHT * 3.2)
        self.play(FadeIn(cost), run_time=0.8)

        # Beat 6: end of part one
        self.beat(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        f, levers = speed_formula(), lever_list()
        self.play(FadeIn(f), FadeIn(levers[0]), run_time=1.0)
        self.cue("reads about a tenth")
        tenth = T("your model: 2.95 B of 34.7 B parameters per token", 24, C_GOLD).next_to(f, DOWN, buff=0.4)
        self.play(FadeIn(tenth), run_time=0.6)
        self.cue("In part two")
        brace = Brace(levers[1:], RIGHT, color=C_GREY)
        p2 = T("part two", 26, C_GREY).next_to(brace, RIGHT, buff=0.2)
        self.play(FadeIn(levers[1:], shift=RIGHT * 0.2, lag_ratio=0.4), GrowFromCenter(brace), FadeIn(p2),
                  run_time=1.2)
        self.end(tail=2.0)
