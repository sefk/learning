from kit.scene import *

from data import MATH, QUANT, WEIGHTS
from scenes_a import bar
from scenes_b import chip


def number_line_group(weights, lo, hi, length=11, y=0.0):
    """A horizontal axis with one dot per weight."""
    axis = NumberLine(x_range=[lo, hi, (hi - lo) / 4], length=length, color=C_GREY, include_ticks=False)
    axis.move_to(UP * y)
    dots = VGroup(*[Dot(axis.n2p(w), radius=0.055, color=C_BLUE) for w in weights])
    # spread dots vertically a little so overlapping weights stay visible
    for i, d in enumerate(dots):
        d.shift(UP * (0.12 * ((i * 7) % 5 - 2)))
    return axis, dots


class Bits(VScene):
    def construct(self):
        w = WEIGHTS["weights"]
        q4 = WEIGHTS["q4"]
        q2 = WEIGHTS["q2"]

        # Beat 0: a weight is a 16-bit number
        self.beat(0)
        val = M(f"{w[3]:+.6f}", 40).move_to(UP * 1.4)
        bits16 = VGroup(*[Square(0.4, stroke_color=C_GREY, stroke_width=1.5) for _ in range(16)]) \
            .arrange(RIGHT, buff=0.05).next_to(val, DOWN, buff=0.4)
        l16 = T("16 bits", 24, C_GREY).next_to(bits16, RIGHT, buff=0.3)
        self.play(FadeIn(val), Create(bits16, lag_ratio=0.05), FadeIn(l16), run_time=1.2)
        self.cue("Quantization replaces")
        bits4 = VGroup(*[Square(0.4, stroke_color=C_PURPLE, stroke_width=2, fill_color=C_PURPLE, fill_opacity=0.4)
                         for _ in range(4)]).arrange(RIGHT, buff=0.05).next_to(bits16, DOWN, buff=0.8)
        l4 = T("4-bit integer", 24, C_PURPLE).next_to(bits4, RIGHT, buff=0.3)
        self.play(TransformFromCopy(bits16[:4], bits4), FadeIn(l4), run_time=1.0)
        self.cue("plus a little shared")
        sh = T("+ a little shared information per group", 24, C_GREY).next_to(bits4, DOWN, buff=0.4)
        self.play(FadeIn(sh), run_time=0.6)

        # Beat 1: group of 64, sixteen levels, snap
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        lo, hi = min(w), max(w)
        pad = (hi - lo) * 0.06
        axis, dots = number_line_group(w, lo - pad, hi + pad, y=0.3)
        title = T("64 real weights: layer 20, expert 0, down-projection (from your 8-bit build)", 22, C_GREY) \
            .to_edge(UP, buff=0.5)
        self.cue("Take sixty-four")
        self.play(FadeIn(title), Create(axis), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.02),
                  run_time=1.6)
        self.cue("Find their smallest")
        lo_m = DashedLine(axis.n2p(lo) + DOWN * 0.6, axis.n2p(lo) + UP * 0.9, color=C_YELLOW)
        hi_m = DashedLine(axis.n2p(hi) + DOWN * 0.6, axis.n2p(hi) + UP * 0.9, color=C_YELLOW)
        lol = M(f"{lo:+.4f}", 18, C_YELLOW).next_to(lo_m, DOWN, buff=0.1)
        hil = M(f"{hi:+.4f}", 18, C_YELLOW).next_to(hi_m, DOWN, buff=0.1)
        self.play(Create(lo_m), Create(hi_m), FadeIn(lol), FadeIn(hil), run_time=0.8)
        self.cue("sixteen evenly spaced")
        step = q4["step"]
        levels = VGroup(*[Line(axis.n2p(q4["offset"] + k * step) + DOWN * 0.45,
                               axis.n2p(q4["offset"] + k * step) + UP * 0.75, color=C_PURPLE, stroke_width=1.5,
                               stroke_opacity=0.7) for k in range(16)])
        self.play(Create(levels, lag_ratio=0.05), run_time=1.0)
        self.cue("Snap every weight")
        snapped = [d.animate.move_to([axis.n2p(v)[0], d.get_y(), 0]).set_color(C_PURPLE)
                   for d, v in zip(dots, q4["dequantized"])]
        self.play(*snapped, run_time=1.2)
        self.cue("store just the level")
        codes = M(" ".join(f"{q:x}" for q in q4["levels"][:32]) + " …", 20, C_PURPLE).move_to(DOWN * 1.5)
        cl = T("stored: one 4-bit level per weight (hex)", 20, C_GREY).next_to(codes, DOWN, buff=0.15)
        self.play(FadeIn(codes), FadeIn(cl), run_time=0.8)
        self.cue("Keep the starting point")
        meta = VGroup(M(f"offset {q4['offset']:+.5f}", 20, C_YELLOW), M(f"step {step:.6f}", 20, C_YELLOW)) \
            .arrange(RIGHT, buff=0.6).move_to(DOWN * 2.6)
        ml = T("+ per group, 16 bits each", 20, C_GREY).next_to(meta, DOWN, buff=0.12)
        self.play(FadeIn(meta), FadeIn(ml), run_time=0.8)

        # Beat 2: 4.5 bits per weight
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        eq = VGroup(T("(64 × 4 + 32) ÷ 64", 36), T("=", 36, C_GREY), T("4.5 bits per weight", 36, C_YELLOW)) \
            .arrange(RIGHT, buff=0.3).move_to(UP * 0.8)
        self.play(Write(eq), run_time=1.6)
        self.cue("Your thirty-five")
        fit = T(f"34.7 B parameters × 4.5 bits = {QUANT['4-bit (published)']['gb']} GB", 32).move_to(DOWN * 0.8)
        self.play(FadeIn(fit), run_time=0.8)

        # Beat 3: each bit removed doubles the step
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        rows = VGroup()
        for i, (name, n, err) in enumerate((("8-bit", 256, None), ("4-bit", 16, q4["rms_error"] / q4["rms_weight"]),
                                            ("2-bit", 4, q2["rms_error"] / q2["rms_weight"]))):
            y = 1.6 - i * 1.6
            ax = Line(LEFT * 4.5, RIGHT * 4.5, color=C_GREY).move_to(UP * y)
            ticks = VGroup(*[Line(UP * 0.25, DOWN * 0.25, stroke_width=1 if n > 16 else 2, color=C_PURPLE)
                             .move_to(ax.point_from_proportion(k / (n - 1))) for k in range(n)])
            lab = T(f"{name}: {n} levels", 24).next_to(ax, LEFT, buff=0.3)
            e = T("" if err is None else f"typical error {err:.0%} of a weight", 20, C_GREY) \
                .next_to(ax, DOWN, buff=0.3)
            rows.add(VGroup(ax, ticks, lab, e))
        rows.shift(RIGHT * 0.8 + DOWN * 0.5)
        half = T("every weight off by up to half a step", 26, C_GREY).to_edge(UP, buff=0.3)
        self.play(FadeIn(half), run_time=0.6)
        self.cue("doubles the step")
        dbl = T("one bit fewer → step × 2 → error × 2", 26, C_YELLOW).next_to(half, DOWN, buff=0.15)
        self.play(FadeIn(dbl), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.3), run_time=1.5)
        for phrase, row in zip(["Eight bits has", "Four bits has", "Two bits has"], rows):
            self.cue(phrase)
            self.play(Indicate(row[2], color=C_YELLOW), run_time=0.8)

        # Beat 4: routers stay at 8 bits
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        router = chip("router: 8-bit", C_YELLOW, 30).move_to(UP * 1.0)
        experts = VGroup(*[Square(0.24, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.45) for _ in range(64)]) \
            .arrange_in_grid(4, 16, buff=0.05).move_to(DOWN * 0.6)
        el = T("experts, attention: 4-bit", 24, C_GOLD).next_to(experts, DOWN, buff=0.25)
        self.play(FadeIn(router), FadeIn(experts), FadeIn(el), run_time=0.8)
        self.cue("a small error there")
        wrong = experts[37]
        self.play(experts[12].animate.set_fill(C_GREEN, opacity=1), run_time=0.4)
        self.play(experts[12].animate.set_fill(C_GOLD, opacity=0.45), wrong.animate.set_fill(C_RED, opacity=1),
                  run_time=0.6)
        wl = T("wrong expert", 22, C_RED).next_to(experts, RIGHT, buff=0.3)
        self.play(FadeIn(wl), run_time=0.4)

        # Beat 5: the bench: 4 vs 8 bits
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("MMLU, your bench: 4-bit vs 8-bit, 500 questions each", 24, C_GREY).to_edge(UP, buff=0.5)
        pairs = [("3.6-27B", 86.2, 85.8), ("3.6-35B-A3B", 83.8, 84.8), ("3.8-27B", 78.8, 81.4)]
        g = VGroup()
        for i, (name, a, b) in enumerate(pairs):
            y = 1.3 - i * 1.2
            b4 = bar(a, 100, 7, C_PURPLE, height=0.3).move_to([0, y + 0.18, 0]).align_to(LEFT * 2.5, LEFT)
            b8 = bar(b, 100, 7, C_GREY, height=0.3).move_to([0, y - 0.18, 0]).align_to(LEFT * 2.5, LEFT)
            g.add(VGroup(b4, b8, T(name, 22).next_to(VGroup(b4, b8), LEFT, buff=0.3),
                         T(f"{a}", 18, C_PURPLE).next_to(b4, RIGHT, buff=0.1),
                         T(f"{b}", 18, C_GREY).next_to(b8, RIGHT, buff=0.1)))
        key = VGroup(chip("4-bit", C_PURPLE, 20), chip("8-bit", C_GREY, 20)).arrange(RIGHT, buff=0.3) \
            .next_to(g, DOWN, buff=0.3)
        self.play(FadeIn(title), FadeIn(g), FadeIn(key), run_time=1.0)
        self.cue("eight bits scored")
        pooled = T("pooled over 1,500: 8-bit +1.07 points, standard error 1.36", 26, C_YELLOW) \
            .to_edge(DOWN, buff=0.5)
        self.play(FadeIn(pooled), run_time=0.7)
        self.cue("indistinguishable")
        self.play(Indicate(pooled, color=C_YELLOW), run_time=1.0)
        self.end()


class TwoBits(VScene):
    def construct(self):
        # Beat 0: the experiment
        self.beat(0)
        src = chip("8-bit build", C_GREY, 28).move_to(LEFT * 4.5 + UP * 0.5)
        outs = VGroup(*[chip(b, C_PURPLE, 26) for b in ("4-bit", "3-bit", "2-bit")]).arrange(DOWN, buff=0.3) \
            .move_to(RIGHT * 0.5 + UP * 0.5)
        arrows = VGroup(*[Arrow(src.get_right(), o.get_left(), buff=0.15, color=C_GREY) for o in outs])
        test = T("→ 500 MMLU questions (your bench's set), thinking off", 24, C_GREY).move_to(DOWN * 1.8)
        self.cue("I took the")
        self.play(FadeIn(src), run_time=0.6)
        self.cue("re-rounded it")
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(o) for o in outs], lag_ratio=0.2), run_time=1.2)
        self.cue("then scored")
        self.play(FadeIn(test), run_time=0.6)

        # Beat 1: uniform rounding results
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        ax = Axes(x_range=[8, 40, 4], y_range=[20, 90, 10], x_length=9.5, y_length=5.2, tips=False,
                  axis_config={"color": C_GREY, "include_ticks": True}).move_to(DOWN * 0.3 + RIGHT * 0.4)
        xl = T("gigabytes", 22, C_GREY).next_to(ax.x_axis, DOWN, buff=0.45)
        yl = T("MMLU %", 22, C_GREY).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.55)
        xt = VGroup(*[T(f"{v}", 18, C_GREY).next_to(ax.c2p(v, 20), DOWN, buff=0.15) for v in range(8, 41, 8)])
        yt = VGroup(*[T(f"{v}", 18, C_GREY).next_to(ax.c2p(8, v), LEFT, buff=0.15) for v in range(20, 91, 10)])
        chance = DashedLine(ax.c2p(8, 25), ax.c2p(40, 25), color=C_RED, stroke_width=2)
        cl = T("guessing: 25%", 20, C_RED).next_to(ax.c2p(40, 25), UP, buff=0.1).shift(LEFT * 0.8)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(xt), FadeIn(yt), run_time=1.0)
        self.play(Create(chance), FadeIn(cl), run_time=0.6)

        def point(name, color, label, direction=RIGHT, at=None):
            """A result dot; with `at` (GB, %), its label sits there with a leader line."""
            v = QUANT[name]
            d = Dot(ax.c2p(v["gb"], 100 * v["mmlu"]), color=color, radius=0.1)
            lab = T(f"{label}  {100 * v['mmlu']:.1f}%", 20, color)
            if at is None:
                return VGroup(d, lab.next_to(d, direction, buff=0.15))
            lab.move_to(ax.c2p(*at), aligned_edge=LEFT)
            lead = Line(d.get_center(), lab.get_left() + LEFT * 0.1, color=color, stroke_width=1.5, buff=0.12)
            return VGroup(d, lab, lead)

        uniform = [("8-bit", "8-bit", UP), ("4-bit", "4-bit", UP), ("3-bit", "3-bit", RIGHT), ("2-bit", "2-bit", RIGHT)]
        pts = {}
        for phrase, (name, label, direction) in zip(["eighty-five point six", "eighty-five at four", "Three bits",
                                                     "And two bits"], uniform):
            self.cue(phrase)
            pts[name] = point(name, C_PURPLE, label, direction)
            self.play(FadeIn(pts[name], scale=1.3), run_time=0.6)
        line = VMobject(color=C_PURPLE, stroke_width=2).set_points_as_corners(
            [pts[n][0].get_center() for n in ("2-bit", "3-bit", "4-bit", "8-bit")])
        self.play(Create(line), run_time=0.8)
        self.ax, self.pts = ax, pts

        # Beat 2: what they write
        self.beat(2)
        chart = Group(*self.mobjects)
        self.play(chart.animate.scale(0.55).to_edge(LEFT, buff=0.3).to_edge(UP, buff=0.3), run_time=0.8)

        def sample(name, label, color, n=120):
            text = QUANT[name]["sample"].replace("**", "").replace("\n", " ")[:n] + "…"
            body = Paragraph(*[text[i:i + 52] for i in range(0, len(text), 52)], font=SERIF, font_size=18,
                             line_spacing=0.6, color=WHITE)
            head = T(label, 20, color)
            return VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.1)

        s3 = sample("3-bit", "3-bit, 75.4%: fluent and correct", C_PURPLE)
        s2 = sample("2-bit", "2-bit, 28.0%", C_RED)
        s32 = sample("2-bit, groups of 32", "2-bit in groups of 32, 34.4%: fluent, but", C_GOLD)
        col = VGroup(s3, s2, s32).arrange(DOWN, aligned_edge=LEFT, buff=0.35).to_edge(RIGHT, buff=0.4)
        self.cue("the three-bit")
        self.play(FadeIn(s3), run_time=0.8)
        self.cue("The two-bit model starts")
        self.play(FadeIn(s2), run_time=0.8)
        self.cue("And a finer")
        self.play(FadeIn(s32), run_time=0.8)
        self.cue("Fluent output")
        warn = T("fluent ≠ fine", 30, C_YELLOW).next_to(chart, DOWN, buff=0.5)
        self.play(FadeIn(warn), run_time=0.6)

        # Beat 3: crush only the experts
        self.beat(3)
        self.play(FadeOut(col), FadeOut(warn), run_time=0.5)
        self.play(chart.animate.scale(1 / 0.55).move_to(DOWN * 0.3 + RIGHT * 0.4), run_time=0.8)
        self.cue("crush only")
        mixed = point("2-bit experts, 8-bit rest", C_GOLD, "2-bit experts, rest 8-bit", at=(17, 45))
        self.play(FadeIn(mixed, scale=1.4), run_time=0.8)
        self.cue("smaller than")
        three = self.pts["3-bit"][0]
        arr = Arrow(three.get_center(), mixed[0].get_center(), buff=0.15, color=C_YELLOW)
        self.play(GrowArrow(arr), Indicate(three, color=C_YELLOW), run_time=1.0)
        self.cue("The damage at two bits")
        m3 = point("3-bit experts, 8-bit rest", C_GOLD, "3-bit experts, rest 8-bit", at=(24, 74))
        self.play(FadeIn(m3), run_time=0.6)
        moe = MATH["moe"]
        share = 256 * 40 * moe["params_per_expert_m"] / 1e3 / moe["params_total_b"]  # routed experts' share
        note = T(f"experts: {share:.0%} of the bytes", 24, C_GOLD).to_corner(UR, buff=0.5)
        self.cue("The experts are")
        self.play(FadeIn(note), run_time=0.6)

        # Beat 4: real formats; the rule of thumb
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        ideas = VGroup(*[VGroup(Dot(color=C_PURPLE, radius=0.08), T(s, 28)).arrange(RIGHT, buff=0.3) for s in (
            "measure which weights matter (importance)",
            "a precision per tensor",
            "codebooks instead of evenly spaced levels",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(UP * 1.4)
        for phrase, idea in zip(["They measure", "give each tensor", "and use cleverer"], ideas):
            self.cue(phrase)
            self.play(FadeIn(idea, shift=RIGHT * 0.2), run_time=0.6)
        self.cue("So when")
        q = T("a two-bit build: where did its bits go?", 30, C_YELLOW).move_to(DOWN * 0.4)
        self.play(FadeIn(q), run_time=0.6)
        self.cue("The general rule")
        rules = VGroup(T("same memory: a bigger model at 3–4 bits beats a smaller one at 8", 24),
                       T("bigger models tolerate fewer bits; below ~3, quality falls fast", 24)) \
            .arrange(DOWN, buff=0.2).move_to(DOWN * 2.1)
        self.play(FadeIn(rules[0]), run_time=0.6)
        self.cue("and that bigger models")
        self.play(FadeIn(rules[1]), run_time=0.6)

        # Beat 5: binary and ternary
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        rng = np.random.default_rng(1)
        signs = VGroup(*[T("+" if rng.random() > 0.5 else "−", 26, C_GREY) for _ in range(48)]) \
            .arrange_in_grid(6, 8, buff=0.25).move_to(LEFT * 3.5)
        sl = T("1 bit: just the sign", 24, C_RED).next_to(signs, DOWN, buff=0.3)
        self.cue("just the sign")
        self.play(FadeIn(signs, lag_ratio=0.02), FadeIn(sl), run_time=1.0)
        self.cue("destroys")
        self.play(Create(Cross(signs, stroke_color=C_RED, stroke_width=5)), run_time=0.6)
        tern = VGroup(*[T(str(rng.choice(["−1", "0", "+1"])), 24, C_TEAL) for _ in range(48)]) \
            .arrange_in_grid(6, 8, buff=0.22).move_to(RIGHT * 3.3)
        tl = T("BitNet: −1, 0, +1 ≈ 1.58 bits, trained that way", 24, C_TEAL).next_to(tern, DOWN, buff=0.3)
        self.cue("BitNet")
        self.play(FadeIn(tern, lag_ratio=0.02), FadeIn(tl), run_time=1.0)
        self.cue("Multiplication then")
        add = T("multiply → add", 28, C_YELLOW).next_to(tern, UP, buff=0.3)
        self.play(FadeIn(add), run_time=0.6)
        self.end()
