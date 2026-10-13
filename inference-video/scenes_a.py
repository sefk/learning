from kit.scene import *

from data import MATH, MEASURED, ROUTING


def model_card(name, sub, color, width=5.2):
    title = M(name, 26, color)
    lines = VGroup(*[T(s, 24, C_GREY) for s in sub]).arrange(DOWN, buff=0.12)
    body = VGroup(title, lines).arrange(DOWN, buff=0.25)
    box = RoundedRectangle(width=width, height=body.height + 0.6, corner_radius=0.15,
                           stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.06)
    return VGroup(box, body)


def bar(value, vmax, length, color, height=0.38, op=0.85):
    w = max(length * value / vmax, 0.02)
    return Rectangle(width=w, height=height, stroke_width=0, fill_color=color, fill_opacity=op)


class Hook(VScene):
    def construct(self):
        # Beat 0: two models, one machine
        self.beat(0)
        mac = T("Mac Studio · M1 Max · 64 GB unified memory", 26, C_GREY).to_edge(UP, buff=0.5)
        dense = model_card("Qwen3.6-27B", ["dense", "4-bit"], C_BLUE).move_to(LEFT * 3.4 + UP * 1.3)
        moe = model_card("Qwen3.6-35B-A3B", ["mixture of experts", "4-bit"], C_GOLD).move_to(RIGHT * 3.4 + UP * 1.3)
        self.play(FadeIn(mac), run_time=0.8)
        self.play(FadeIn(dense, shift=UP * 0.2), FadeIn(moe, shift=UP * 0.2), run_time=1.2)

        # Beat 1: parameters and speed
        self.beat(1)
        p1 = T("27 billion parameters", 28).next_to(dense, DOWN, buff=0.35)
        self.play(FadeIn(p1), run_time=0.6)
        self.cue("It writes")
        lanes = VGroup()
        for card, rate, color in ((dense, MEASURED["dense_decode"], C_BLUE), (moe, MEASURED["moe_decode"], C_GOLD)):
            lane = Rectangle(width=5.2, height=0.42, stroke_color=C_DIM, stroke_width=1.5)
            lane.next_to(card, DOWN, buff=1.05)
            lanes.add(lane)
        self.play(Create(lanes[0]), run_time=0.5)
        dense_rate = T(f"{MEASURED['dense_decode']} tokens/s", 28, C_BLUE).next_to(lanes[0], DOWN, buff=0.2)
        self.stream(lanes[0], MEASURED["dense_decode"], C_BLUE, 3.0)
        self.play(FadeIn(dense_rate), run_time=0.5)
        self.cue("The second is")
        p2 = T("35 billion parameters", 28).next_to(moe, DOWN, buff=0.35)
        self.play(FadeIn(p2), Create(lanes[1]), run_time=0.7)
        self.cue("And it writes")
        moe_rate = T(f"{MEASURED['moe_decode']} tokens/s", 28, C_GOLD).next_to(lanes[1], DOWN, buff=0.2)
        self.play(FadeIn(moe_rate), run_time=0.4)
        self.stream(lanes[1], MEASURED["moe_decode"], C_GOLD, 3.0)
        ratio = T(f"{MEASURED['moe_decode'] / MEASURED['dense_decode']:.1f}× faster", 34, C_YELLOW) \
            .next_to(moe_rate, DOWN, buff=0.3)
        self.play(FadeIn(ratio, scale=1.2), run_time=0.6)

        # Beat 2: same quality
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (mac, dense, moe)], run_time=0.6)
        ql = T("knowledge + math score (MMLU + GSM8K), 95% intervals", 22, C_GREY).move_to(DOWN * 0.6)
        ax = NumberLine(x_range=[84, 94, 2], length=9, color=C_GREY).move_to(DOWN * 2.6)
        ax.add(*[T(f"{v}%", 20, C_GREY).next_to(ax.n2p(v), DOWN, buff=0.2) for v in range(84, 95, 2)])
        self.play(FadeIn(ql), Create(ax), run_time=0.8)
        rows = []
        for i, (name, score, color) in enumerate((("dense", 89.6, C_BLUE), ("MoE", 88.1, C_GOLD))):
            y = -1.3 - i * 0.6
            ci = Line(ax.n2p(score - 2.2) + UP * (y + 2.6), ax.n2p(score + 2.2) + UP * (y + 2.6),
                      color=color, stroke_width=4)
            dot = Dot(ax.n2p(score) + UP * (y + 2.6), color=color, radius=0.09)
            lab = T(f"{name} {score}%", 22, color).next_to(ci, LEFT, buff=0.3)
            rows.append(VGroup(ci, dot, lab))
        self.play(*[FadeIn(r) for r in rows], run_time=1.0)
        self.cue("So the bigger")
        q = T("?", 120, C_YELLOW).move_to(RIGHT * 5.6 + DOWN * 1.8)
        self.play(FadeIn(q, scale=1.5), run_time=0.8)

        # Beat 3: roadmap
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        items = ["what limits speed", "what an expert actually is", "what quantization costs",
                 "where the context goes"]
        colors = [C_TEAL, C_GOLD, C_PURPLE, C_BLUE]
        road = VGroup(*[VGroup(Dot(color=c, radius=0.1), T(s, 34)).arrange(RIGHT, buff=0.35)
                        for s, c in zip(items, colors)]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        for phrase, item in zip(["what limits its speed", "what a mixture", "what quantization", "where all your"], road):
            self.cue(phrase)
            self.play(FadeIn(item, shift=RIGHT * 0.3), run_time=0.6)
        self.end()

    def stream(self, lane, rate, color, seconds):
        """Fill a lane with token squares at a rate proportional to tokens/s."""
        n = max(2, round(rate / 67.3 * 28))
        toks = VGroup(*[Square(0.14, stroke_width=0, fill_color=color, fill_opacity=0.85) for _ in range(n)]) \
            .arrange(RIGHT, buff=0.04)
        toks.scale_to_fit_width(min(toks.width, lane.width - 0.2)).move_to(lane).align_to(lane, LEFT).shift(RIGHT * 0.1)
        self.play(LaggedStart(*[FadeIn(t) for t in toks], lag_ratio=1.0), run_time=seconds, rate_func=linear)
        return toks


class MemoryWall(VScene):
    def construct(self):
        # Beat 0: one token reads every weight
        self.beat(0)
        mem = RoundedRectangle(width=5.0, height=4.4, corner_radius=0.2, stroke_color=C_BLUE, stroke_width=2)
        mem.move_to(LEFT * 4.0 + DOWN * 0.3)
        mem_l = T("unified memory", 24, C_BLUE).next_to(mem, UP, buff=0.15)
        grid = VGroup(*[Square(0.19, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.35)
                        for _ in range(20 * 16)]).arrange_in_grid(16, 20, buff=0.035).move_to(mem)
        wl = T("weights", 22, C_GREY).next_to(mem, DOWN, buff=0.15)
        gpu = RoundedRectangle(width=3.2, height=2.2, corner_radius=0.2, stroke_color=C_GREEN, stroke_width=2)
        gpu.move_to(RIGHT * 4.3 + DOWN * 0.3)
        gpu_l = T("GPU", 30, C_GREEN).move_to(gpu)
        self.play(Create(mem), FadeIn(mem_l), FadeIn(grid, lag_ratio=0.002), FadeIn(wl), run_time=1.5)
        self.play(Create(gpu), FadeIn(gpu_l), run_time=0.8)
        self.cue("every weight")
        pipe = Arrow(mem.get_right(), gpu.get_left(), buff=0.1, color=C_GREY, stroke_width=6)
        self.play(GrowArrow(pipe), run_time=0.6)
        rows = [VGroup(*grid[r * 20:(r + 1) * 20]) for r in range(16)]
        self.play(LaggedStart(*[r.animate.set_fill(C_YELLOW, opacity=0.8) for r in rows], lag_ratio=0.15),
                  run_time=2.5)
        self.play(grid.animate.set_fill(C_BLUE, opacity=0.35), run_time=0.5)

        # Beat 1: bytes / bandwidth = ceiling
        self.beat(1)
        gb = MATH["dense"]["gb_read_per_token_4bit"]
        per_tok = T(f"{gb} GB per token", 28, C_YELLOW).next_to(pipe, UP, buff=0.4)
        self.play(FadeIn(per_tok), run_time=0.7)
        self.cue("This machine")
        bw = T("≤ 400 GB/s", 28, C_GREY).next_to(pipe, DOWN, buff=0.4)
        self.play(FadeIn(bw), run_time=0.7)
        self.cue("Divide")
        eq = VGroup(T("400 GB/s", 32), T("÷", 32, C_GREY), T(f"{gb} GB", 32), T("=", 32, C_GREY),
                    T(f"{MATH['dense']['decode_ceiling_4bit']:.0f} tokens/s", 36, C_YELLOW)).arrange(RIGHT, buff=0.25)
        eq.to_edge(UP, buff=0.4)
        self.play(FadeOut(mem_l), Write(eq), run_time=1.5)
        self.cue("no matter")
        self.play(Indicate(gpu_l, color=C_GREEN), run_time=1.0)

        # Beat 2: two thirds of the ceiling; the GPU waits
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not eq], run_time=0.6)
        ceil = MATH["dense"]["decode_ceiling_4bit"]
        b_ceiling = bar(ceil, ceil, 9, C_DIM).move_to(UP * 1.0).align_to(LEFT * 4.5, LEFT)
        b_meas = bar(MEASURED["dense_decode"], ceil, 9, C_BLUE).move_to(UP * 0.3).align_to(LEFT * 4.5, LEFT)
        l1 = T("ceiling", 22, C_GREY).next_to(b_ceiling, LEFT, buff=0.2)
        l2 = T("measured", 22, C_BLUE).next_to(b_meas, LEFT, buff=0.2)
        v2 = T(f"{MEASURED['dense_decode']} tokens/s  ({MATH['dense']['decode_share_of_ceiling']:.0%})", 22, C_BLUE) \
            .next_to(b_meas, RIGHT, buff=0.2)
        self.play(GrowFromEdge(b_ceiling, LEFT), FadeIn(l1), run_time=0.8)
        self.play(GrowFromEdge(b_meas, LEFT), FadeIn(l2), FadeIn(v2), run_time=0.8)
        self.cue("The GPU itself")
        util = VGroup(T("GPU arithmetic in use during decode (roughly)", 24, C_GREY),
                      VGroup(Rectangle(width=6, height=0.35, stroke_color=C_GREY, stroke_width=1.5),
                             )).arrange(DOWN, buff=0.2).move_to(DOWN * 1.4)
        fill = Rectangle(width=0.35, height=0.35, stroke_width=0, fill_color=C_GREEN, fill_opacity=0.8) \
            .align_to(util[1], LEFT).match_y(util[1])
        self.play(FadeIn(util), GrowFromEdge(fill, LEFT), run_time=0.8)
        self.cue("Each weight")
        fma = VGroup(M("acc += w * x", 30), T("then w is dropped until the next token", 26, C_GREY, slant=ITALIC)) \
            .arrange(RIGHT, buff=0.5).move_to(DOWN * 2.8)
        self.play(FadeIn(fma, shift=UP * 0.2), run_time=0.8)

        # Beat 3: prefill reuses each weight across the prompt
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("prefill: the whole prompt at once", 32, C_TEAL).to_edge(UP, buff=0.5)
        w = Square(0.6, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.85).move_to(LEFT * 4.5)
        wl = T("one weight,\nfetched once", 22, C_GREY).next_to(w, DOWN, buff=0.2)
        toks = VGroup(*[Square(0.22, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.7) for _ in range(96)]) \
            .arrange_in_grid(8, 12, buff=0.06).move_to(RIGHT * 2.2)
        tl = T("thousands of prompt tokens", 22, C_GREY).next_to(toks, DOWN, buff=0.2)
        self.play(FadeIn(title), FadeIn(w), FadeIn(wl), run_time=0.8)
        self.play(FadeIn(toks, lag_ratio=0.01), FadeIn(tl), run_time=1.0)
        self.cue("so each weight")
        lines = VGroup(*[Line(w.get_right(), t.get_center(), stroke_width=1, color=C_YELLOW, stroke_opacity=0.35)
                         for t in toks[::3]])
        self.play(Create(lines, lag_ratio=0.02), run_time=1.5)
        self.cue("Now the limit")
        lim = T("limit: arithmetic, not memory", 30, C_YELLOW).to_edge(DOWN, buff=1.2)
        self.play(FadeIn(lim), run_time=0.6)
        self.cue("The dense model manages")
        flops = T(f"{MEASURED['dense_prefill']} tokens/s × {MATH['dense']['prefill_gflop_per_token']:.0f} GFLOP per token"
                  f"  ≈  {MATH['dense']['prefill_tflops']:.1f} TFLOP/s", 26).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(flops), run_time=0.8)

        # Beat 4: two regimes
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        head = VGroup(T("", 26), T("decides", 26, C_GREY), T("bound by", 26, C_GREY))
        r1 = VGroup(T("prefill", 32, C_TEAL), T("time to first token", 28), T("compute", 28, C_YELLOW))
        r2 = VGroup(T("decode", 32, C_BLUE), T("streaming speed", 28), T("memory bandwidth", 28, C_YELLOW))
        table = VGroup(head, r1, r2)
        for row in table:
            for j, cell in enumerate(row):
                cell.move_to([-4.2 + j * 4.2, 0, 0])
        head.move_to(UP * 1.4, coor_mask=[0, 1, 0])
        r1.move_to(UP * 0.2, coor_mask=[0, 1, 0])
        r2.move_to(DOWN * 1.0, coor_mask=[0, 1, 0])
        self.play(FadeIn(head), run_time=0.5)
        self.play(FadeIn(r1, shift=RIGHT * 0.2), run_time=0.7)
        self.cue("Decode, which")
        self.play(FadeIn(r2, shift=RIGHT * 0.2), run_time=0.7)

        # Beat 5: two levers
        self.beat(5)
        self.play(table.animate.scale(0.7).to_edge(UP, buff=0.4), run_time=0.8)
        lever1 = VGroup(T("touch fewer weights per token", 32), T("→ mixture of experts", 32, C_GOLD)) \
            .arrange(DOWN, buff=0.15)
        lever2 = VGroup(T("make each weight smaller", 32), T("→ quantization", 32, C_PURPLE)).arrange(DOWN, buff=0.15)
        levers = VGroup(lever1, lever2).arrange(RIGHT, buff=1.2).move_to(DOWN * 1.0)
        self.cue("Touch fewer")
        self.play(FadeIn(lever1[0]), run_time=0.6)
        self.cue("or make")
        self.play(FadeIn(lever2[0]), run_time=0.6)
        self.cue("The first lever")
        self.play(FadeIn(lever1[1]), run_time=0.6)
        self.cue("The second is")
        self.play(FadeIn(lever2[1]), run_time=0.6)
        self.end()


class Experts(VScene):
    def construct(self):
        dense = MATH["dense"]
        moe = MATH["moe"]

        # Beat 0: a layer is attention + feed-forward
        self.beat(0)
        attn = RoundedRectangle(width=3.4, height=1.0, corner_radius=0.12, stroke_color=C_TEAL,
                                fill_color=C_TEAL, fill_opacity=0.15)
        ffn = RoundedRectangle(width=3.4, height=1.0, corner_radius=0.12, stroke_color=C_GOLD,
                               fill_color=C_GOLD, fill_opacity=0.15)
        layer = VGroup(attn, ffn).arrange(UP, buff=0.35).move_to(LEFT * 3.8)
        al = T("attention", 26, C_TEAL).move_to(attn)
        fl = T("feed-forward", 26, C_GOLD).move_to(ffn)
        cap = T("one transformer layer", 22, C_GREY).next_to(layer, DOWN, buff=0.3)
        self.play(FadeIn(layer), FadeIn(al), FadeIn(cap), run_time=1.0)
        self.cue("And a feed-forward")
        self.play(FadeIn(fl), run_time=0.6)
        self.cue("In the dense model")
        parts = [("feed-forward", dense["ffn_total_b"], C_GOLD), ("attention", dense["attention_b"], C_TEAL),
                 ("embeddings + output", 2 * dense["output_head_b"], C_GREY)]
        bars = VGroup()
        for i, (name, v, c) in enumerate(parts):
            b = bar(v, 20, 5.0, c).move_to([1.2, 1.0 - i * 0.8, 0]).align_to([0.8, 0, 0], LEFT)
            lab = T(f"{name}  {v:.1f} B", 24, c).next_to(b, UP, buff=0.08).align_to(b, LEFT)
            bars.add(VGroup(b, lab))
        title = T("Qwen3.6-27B parameters", 24, C_GREY).next_to(bars, UP, buff=0.4).align_to(bars, LEFT)
        self.play(FadeIn(title), LaggedStart(*[GrowFromEdge(b[0], LEFT) for b in bars], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(b[1]) for b in bars], lag_ratio=0.2), run_time=1.5)

        # Beat 1: chop the FFN into 256 experts
        self.beat(1)
        self.play(FadeOut(bars), FadeOut(title), FadeOut(cap), run_time=0.6)
        experts = VGroup(*[Square(0.24, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.45)
                           for _ in range(256)]).arrange_in_grid(16, 16, buff=0.05).move_to(RIGHT * 2.2)
        self.cue("chops it into many")
        self.play(ReplacementTransform(VGroup(ffn.copy()), experts), run_time=1.5)
        el = T("256 experts", 30, C_GOLD).next_to(experts, UP, buff=0.3)
        self.play(FadeIn(el), run_time=0.5)
        self.cue("Each expert is")
        one = experts[0].copy()
        zoom = VGroup(M("2048", 20), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, color=C_GREY), M("512", 20),
                      Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, color=C_GREY), M("2048", 20)).arrange(RIGHT, buff=0.12)
        zl = T(f"one expert: a small gated MLP, {moe['params_per_expert_m']:.2f} M parameters", 22, C_GREY)
        zg = VGroup(zoom, zl).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.4)
        self.play(Indicate(experts[0], color=C_YELLOW, scale_factor=2), FadeIn(zg), run_time=1.2)

        # Beat 2: the router picks the top 8
        self.beat(2)
        self.play(FadeOut(zg), run_time=0.4)
        tok = token_box("token", C_BLUE, 24).move_to(LEFT * 5.4 + DOWN * 2.6)
        router = RoundedRectangle(width=1.6, height=0.8, corner_radius=0.1, stroke_color=C_PURPLE,
                                  fill_color=C_PURPLE, fill_opacity=0.2).move_to(LEFT * 1.6 + DOWN * 2.6)
        rl = T("router", 24, C_PURPLE).move_to(router)
        self.play(FadeIn(tok), FadeIn(router), FadeIn(rl), run_time=0.8)
        self.play(GrowArrow(Arrow(tok.get_right(), router.get_left(), buff=0.1, color=C_GREY)), run_time=0.5)
        self.cue("gives every expert")
        rng = np.random.default_rng(3)
        scores = rng.random(256) ** 3
        self.play(*[sq.animate.set_fill(C_PURPLE, opacity=0.15 + 0.75 * s) for sq, s in zip(experts, scores)],
                  run_time=1.2)
        self.cue("The top eight")
        top = np.argsort(-scores)[:8]
        self.play(*[sq.animate.set_fill(C_DIM, opacity=0.35) for i, sq in enumerate(experts) if i not in top],
                  *[experts[i].animate.set_fill(C_YELLOW, opacity=1.0) for i in top], run_time=1.0)
        self.cue("Those eight experts run")
        out = Circle(0.3, color=C_YELLOW).move_to(RIGHT * 5.8 + DOWN * 2.6)
        plus = T("Σ", 30, C_YELLOW).move_to(out)
        arrows = VGroup(*[Arrow(experts[i].get_center(), out.get_center(), buff=0.3, color=C_YELLOW,
                                stroke_width=2, max_tip_length_to_length_ratio=0.05) for i in top])
        self.play(FadeIn(out), FadeIn(plus), LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.1),
                  run_time=1.4)
        self.cue("The other two hundred")
        idle = T("248 idle", 26, C_GREY).next_to(experts, LEFT, buff=0.3).shift(UP * 1.2)
        self.play(FadeIn(idle), run_time=0.6)

        # Beat 3: the shared expert
        self.beat(3)
        shared = RoundedRectangle(width=1.6, height=0.6, corner_radius=0.1, stroke_color=C_GREEN,
                                  fill_color=C_GREEN, fill_opacity=0.5).move_to(RIGHT * 2.2 + DOWN * 2.6)
        sl = T("shared", 22).move_to(shared)
        self.play(FadeIn(shared), FadeIn(sl), GrowArrow(Arrow(shared.get_right(), out.get_left(), buff=0.1,
                                                                 color=C_GREEN)), run_time=1.0)
        self.cue("So per token")
        nine = T("8 routed + 1 shared = 9 per token, per layer", 28, C_YELLOW).to_edge(UP, buff=0.3)
        self.play(FadeOut(el), FadeIn(nine), run_time=0.8)

        # Beat 4: forty layers, fresh choices
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        strips = VGroup()
        for layer_i in range(40):
            row = VGroup(*[Rectangle(width=0.042, height=0.12, stroke_width=0, fill_color=C_DIM, fill_opacity=0.6)
                           for _ in range(256)]).arrange(RIGHT, buff=0.006)
            strips.add(row)
        strips.arrange(DOWN, buff=0.04).move_to(DOWN * 0.2)
        self.play(FadeIn(strips), run_time=0.8)
        picks = ROUTING["sentence_routing_by_layer"]  # real choices for one token, every layer
        lit = [strips[li][e] for li, layer_picks in enumerate(picks) for e in layer_picks]
        self.play(LaggedStart(*[c.animate.set_fill(C_YELLOW, opacity=1.0) for c in lit], lag_ratio=0.01),
                  run_time=3.0)
        cap = T("one real token (“keeper”) through all 40 layers: 8 of 256 experts each", 22, C_GREY) \
            .next_to(strips, DOWN, buff=0.25)
        self.play(FadeIn(cap), run_time=0.6)
        self.cue("three hundred and twenty")
        n = T("40 × 8 = 320 routing decisions", 32, C_YELLOW).to_edge(UP, buff=0.3)
        self.play(FadeIn(n), run_time=0.8)

        # Beat 5: stored vs active
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        stored = bar(moe["params_total_b"], moe["params_total_b"], 10, C_DIM, height=0.7) \
            .move_to(UP * 0.8).align_to(LEFT * 5, LEFT)
        active = bar(moe["params_active_b"], moe["params_total_b"], 10, C_YELLOW, height=0.7) \
            .move_to(DOWN * 0.6).align_to(LEFT * 5, LEFT)
        s_l = T(f"stored: {moe['params_total_b']:.1f} B", 30).next_to(stored, UP, buff=0.15).align_to(stored, LEFT)
        a_l = T(f"active per token: {moe['params_active_b']:.2f} B", 30, C_YELLOW) \
            .next_to(active, UP, buff=0.15).align_to(active, LEFT)
        self.play(GrowFromEdge(stored, LEFT), FadeIn(s_l), run_time=1.0)
        self.cue("But a single")
        self.play(GrowFromEdge(active, LEFT), FadeIn(a_l), run_time=1.0)
        self.cue("That's what")
        name = VGroup(M("35B", 44, WHITE), M("-", 44, C_GREY), M("A3B", 44, C_YELLOW)).arrange(RIGHT, buff=0.08) \
            .move_to(DOWN * 2.3)
        self.play(FadeIn(name), run_time=0.8)
        self.cue("Three billion active")
        self.play(Indicate(name[2], color=C_YELLOW), run_time=1.0)

        # Beat 6: load balancing
        self.beat(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        load = sorted(ROUTING["mid_layer_load"], reverse=True)
        total = sum(load)
        collapsed = [total * 0.3, total * 0.25, total * 0.2, total * 0.12, total * 0.08] + [total * 0.05 / 251] * 251

        def histogram(values, color):
            h = VGroup(*[Rectangle(width=0.019, height=max(0.01, 2.4 * v / (total * 0.3)), stroke_width=0,
                                   fill_color=color, fill_opacity=0.85) for v in values])
            h.arrange(RIGHT, buff=0.003, aligned_edge=DOWN)
            base = Line(h.get_corner(DL), h.get_corner(DR), color=C_GREY, stroke_width=1.5)
            return VGroup(base, h)

        real = histogram(load, C_GOLD).move_to(RIGHT * 3.3 + DOWN * 0.8, aligned_edge=DOWN)
        bad = histogram(collapsed, C_RED).move_to(LEFT * 3.3 + DOWN * 0.8, aligned_edge=DOWN)
        used = sum(v > 0 for v in load)
        rl = T(f"your model, layer 20: {used} of 256 experts in use", 22, C_GOLD).next_to(real, DOWN, buff=0.25)
        bl = T("collapsed (schematic)", 22, C_RED).next_to(bad, DOWN, buff=0.25)
        cap = T("share of traffic per expert, busiest first", 20, C_GREY).to_edge(DOWN, buff=0.4)
        self.cue("with one extra")
        pen = T("+ a small penalty when traffic is lopsided", 28, C_PURPLE).to_edge(UP, buff=0.6)
        self.play(FadeIn(pen), run_time=0.8)
        self.cue("Without that")
        self.play(Create(bad[0]), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bad[1]], lag_ratio=0.002),
                  FadeIn(bl), FadeIn(cap), run_time=1.5)
        self.play(Create(real[0]), LaggedStart(*[GrowFromEdge(b, DOWN) for b in real[1]], lag_ratio=0.002),
                  FadeIn(rl), run_time=1.5)
        self.end()
