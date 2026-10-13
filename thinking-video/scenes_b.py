from common import *


def squares(n, color, op=0.55, size=0.16, buff=0.05):
    return VGroup(*[Square(size, stroke_width=0, fill_color=color, fill_opacity=op)
                    for _ in range(n)]).arrange(RIGHT, buff=buff)


class Training(VScene):
    def construct(self):
        # Beat 0: from prompting to RL
        self.beat(0)
        quote = T("“Let’s think step by step.”", 44).move_to(UP * 1.8)
        cite = T("Kojima et al., 2022", 20, C_GREY).next_to(quote, DOWN, buff=0.2)
        self.play(Write(quote), run_time=1.8)
        self.play(FadeIn(cite), run_time=0.5)
        self.at(8.5)
        worked = VGroup(*[M(s, 20, C_GREY) for s in [
            "Example 3.  Solve 2x + 6 = 14.",
            "Subtract 6 from both sides: 2x = 8.",
            "Divide by 2: x = 4.",
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        wl = T("pretraining data is full of worked examples", 24, C_GREY)
        wg = VGroup(wl, worked).arrange(DOWN, buff=0.3).move_to(DOWN * 0.4)
        self.play(FadeIn(wg, shift=UP * 0.2), run_time=1.0)
        self.at(15.0)
        rl = T("reinforcement learning", 44, C_GOLD).to_edge(DOWN, buff=0.8)
        arr = Arrow(wg.get_bottom(), rl.get_top(), buff=0.15, color=C_GOLD)
        self.play(GrowArrow(arr), FadeIn(rl, shift=UP * 0.2), run_time=1.2)

        # Beat 1: a checkable problem, eight attempts
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        prob = VGroup(T("Problem:", 28, C_GREY), M("x² − 5x + 6 = 0.  Largest x?", 26)) \
            .arrange(RIGHT, buff=0.3)
        key = VGroup(T("known answer:", 24, C_GREY), M("3", 26, C_GREEN)).arrange(RIGHT, buff=0.2)
        card = VGroup(prob, key).arrange(RIGHT, buff=0.8).to_edge(UP, buff=0.5)
        self.play(FadeIn(prob), run_time=0.8)
        self.at(5.5)
        self.play(FadeIn(key), run_time=0.6)

        answers = ["3", "2", "3", "3", "6", "3", "2", "3"]
        lengths = [22, 9, 26, 17, 12, 30, 14, 20]
        rows = VGroup()
        for i, (a, n) in enumerate(zip(answers, lengths)):
            y = 1.9 - i * 0.58
            lab = M(f"#{i + 1}", 20, C_GREY).move_to([-6.2, y, 0])
            strip = squares(n, C_GREY).move_to([0, y, 0]).align_to([-5.6, 0, 0], LEFT)
            ans = token_box(a, WHITE, 22).move_to([1.6, y, 0])
            rows.add(VGroup(lab, strip, ans))
        self.at(9.5)
        self.play(LaggedStart(*[FadeIn(r[0]) for r in rows], lag_ratio=0.1), run_time=0.8)
        self.play(LaggedStart(*[Create(r[1], lag_ratio=0.1) for r in rows], lag_ratio=0.12), run_time=2.2)

        # Beat 2: grade only the answers
        self.beat(2)
        think_l = T("thinking", 22, C_GREY).next_to(rows[0][1], UP, buff=0.15).align_to(rows[0][1], LEFT)
        ans_l = T("answer", 22, C_GREY).next_to(rows[0][2], UP, buff=0.15)
        self.play(FadeIn(think_l), run_time=0.5)
        self.at(2.6)
        self.play(FadeIn(ans_l), LaggedStart(*[FadeIn(r[2]) for r in rows], lag_ratio=0.1), run_time=1.2)
        marks = VGroup()
        for r, a in zip(rows, answers):
            ok = a == "3"
            marks.add(T("✓" if ok else "✗", 30, C_GREEN if ok else C_RED).next_to(r[2], RIGHT, buff=0.35))
        self.at(5.0)
        self.play(LaggedStart(*[FadeIn(m, scale=1.4) for m in marks], lag_ratio=0.12), run_time=1.6)
        self.at(8.5)
        strips = VGroup(*[r[1] for r in rows])
        ng = T("not graded", 24, C_GREY, slant=ITALIC).next_to(think_l, RIGHT, buff=0.4)
        self.play(strips.animate.set_opacity(0.25), FadeIn(ng), run_time=1.0)

        # Beat 3: group-relative advantage
        self.beat(3)
        self.play(strips.animate.set_opacity(0.55), FadeOut(ng), run_time=0.6)
        rewards = VGroup(*[M("1" if a == "3" else "0", 22).move_to([3.6, r.get_y(), 0])
                           for r, a in zip(rows, answers)])
        rl = T("reward", 22, C_GREY).next_to(rewards[0], UP, buff=0.15).match_y(ans_l)
        self.play(FadeIn(rewards), FadeIn(rl), run_time=0.8)
        mean = T("group mean = 5/8", 26, C_YELLOW).to_edge(DOWN, buff=0.35).shift(RIGHT * 3.5)
        self.play(FadeIn(mean), run_time=0.6)
        advs = VGroup()
        for r, a in zip(rows, answers):
            ok = a == "3"
            advs.add(M("+0.38" if ok else "−0.62", 22, C_GREEN if ok else C_RED).move_to([5.2, r.get_y(), 0]))
        al = T("advantage", 22, C_GREY).next_to(advs[0], UP, buff=0.15).match_y(ans_l)
        self.at(3.5)
        self.play(FadeIn(advs), FadeIn(al), run_time=0.8)
        self.at(4.5)
        good = [r[1] for r, a in zip(rows, answers) if a == "3"]
        bad = [r[1] for r, a in zip(rows, answers) if a != "3"]
        self.play(*[s.animate.set_fill(C_GREEN, opacity=0.8) for s in good], run_time=1.0)
        ups = VGroup(*[Arrow(DOWN * 0.2, UP * 0.2, buff=0, color=C_GREEN, stroke_width=4,
                             max_tip_length_to_length_ratio=0.5).next_to(s, RIGHT, buff=0.15) for s in good])
        self.play(FadeIn(ups, shift=UP * 0.15), run_time=0.6)
        self.at(7.8)
        self.play(*[s.animate.set_fill(C_RED, opacity=0.8) for s in bad], run_time=1.0)
        downs = VGroup(*[Arrow(UP * 0.2, DOWN * 0.2, buff=0, color=C_RED, stroke_width=4,
                               max_tip_length_to_length_ratio=0.5).next_to(s, RIGHT, buff=0.15) for s in bad])
        self.play(FadeIn(downs, shift=DOWN * 0.15), run_time=0.6)
        self.at(10.5)
        self.play(LaggedStart(*[Indicate(sq, color=C_YELLOW, scale_factor=1.4) for sq in rows[5][1]],
                              lag_ratio=0.08), run_time=2.0)
        rep = T("× many thousands of problems", 26, C_GOLD).to_edge(DOWN, buff=0.35).shift(LEFT * 3)
        self.at(14.0)
        self.play(FadeIn(rep), run_time=0.8)

        # Beat 4: emergent length and behaviors
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        ax = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=5.6, y_length=4.2,
                  tips=False, axis_config={"color": C_GREY, "include_ticks": False}).to_edge(LEFT, buff=1.1).shift(DOWN * 0.3)
        xl = T("RL training steps →", 22, C_GREY).next_to(ax.x_axis, DOWN, buff=0.2)
        yl = T("avg response length →", 22, C_GREY).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=1.0)
        f = lambda x: 1.0 + 0.78 * x + 0.3 * np.sin(3.1 * x) + 0.18 * np.sin(7.7 * x) + 0.12 * np.sin(13 * x)
        curve = ax.plot(f, x_range=[0, 10, 0.02], color=C_GOLD, stroke_width=3)
        self.play(Create(curve), run_time=4.0, rate_func=linear)
        src = T("shape as reported for DeepSeek-R1-Zero (2025); illustrative", 18, C_GREY).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(src), run_time=0.5)
        snippets = [
            (9.2, "Let me verify: 9 − 15 + 6 = 0 ✓"),
            (11.0, "Alternatively, factor it…"),
            (13.2, "Wait, that's not right."),
        ]
        prev = None
        for cue, s in snippets:
            self.at(cue)
            box = token_box(s, C_YELLOW if s.startswith("Wait") else WHITE, 19, 0.15)
            if prev is None:
                box.move_to(RIGHT * 3.6 + UP * 1.6)
            else:
                box.next_to(prev, DOWN, buff=0.45)
            box.align_to(RIGHT * 0.5, LEFT)
            self.play(FadeIn(box, shift=LEFT * 0.3), run_time=0.7)
            prev = box

        # Beat 5: "wait" is reinforced
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        trace = VGroup(
            M("…the roots are 2 and 3, so x = 2.", 26, C_GREY),
            M("Wait, 2 is the smaller root.", 26, C_GREY, t2c={"Wait,": C_YELLOW}),
            M("The largest is x = 3.", 26, C_GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(UP * 0.6)
        self.play(FadeIn(trace[0]), run_time=0.6)
        self.play(FadeIn(trace[1]), run_time=0.6)
        self.play(FadeIn(trace[2]), run_time=0.6)
        self.at(4.5)
        lbl = T("reinforced, not scripted", 36, C_YELLOW).to_edge(DOWN, buff=1.2)
        self.play(FadeIn(lbl, shift=UP * 0.2), run_time=0.8)

        # Beat 6: distillation into local models
        self.beat(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        big = layer_stack(10, w=0.9, h=0.3, color=C_GOLD).move_to(LEFT * 4.5)
        small = layer_stack(5, w=0.55, h=0.3, color=C_BLUE).move_to(RIGHT * 4.5)
        bl = T("large reasoning model", 24, C_GOLD).next_to(big, DOWN)
        sl = T("the model on your machine", 24, C_BLUE).next_to(small, DOWN)
        self.play(FadeIn(big), FadeIn(bl), run_time=0.8)
        self.at(2.5)
        self.play(FadeIn(small), FadeIn(sl), run_time=0.8)
        arr = Arrow(big.get_right(), small.get_left(), buff=0.5, color=C_GREY)
        flow = VGroup(*[squares(6, C_GOLD, 0.7, 0.13, 0.03) for _ in range(3)]).arrange(DOWN, buff=0.12) \
            .next_to(arr, UP, buff=0.2)
        tl = T("reasoning traces", 22, C_GOLD).next_to(flow, UP, buff=0.15)
        self.at(4.5)
        self.play(GrowArrow(arr), FadeIn(flow, shift=RIGHT * 0.4), FadeIn(tl), run_time=1.2)
        d = T("fine-tune (distillation)", 26).next_to(arr, DOWN, buff=0.3)
        self.at(7.0)
        self.play(FadeIn(d), run_time=0.7)
        plus = T("+ its own RL", 26, C_GOLD).next_to(d, DOWN, buff=0.2)
        self.at(10.0)
        self.play(FadeIn(plus), run_time=0.7)
        self.end(1.0)


class Dial(VScene):
    def construct(self):
        # Beat 0: accuracy vs log thinking tokens
        self.beat(0)
        ax = Axes(x_range=[2, 5, 1], y_range=[0, 100, 25], x_length=8, y_length=4.5, tips=False,
                  axis_config={"color": C_GREY}).shift(DOWN * 0.3)
        xlabs = VGroup(*[M(s, 20, C_GREY).next_to(ax.c2p(x, 0), DOWN, buff=0.2)
                         for x, s in zip([2, 3, 4, 5], ["100", "1k", "10k", "100k"])])
        xl = T("thinking tokens (log scale)", 24, C_GREY).next_to(xlabs, DOWN, buff=0.2)
        yl = T("accuracy", 24, C_GREY).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.3)
        self.play(Create(ax), FadeIn(xlabs), FadeIn(xl), FadeIn(yl), run_time=1.5)
        rng = np.random.default_rng(3)
        xs = np.arange(2.0, 5.01, 0.25)
        ys = 18 + 17 * (xs - 2) + rng.normal(0, 2.5, len(xs))
        dots = VGroup(*[Dot(ax.c2p(x, y), color=C_GOLD, radius=0.07) for x, y in zip(xs, ys)])
        self.at(4.0)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.15), run_time=3.0)
        fit = DashedLine(ax.c2p(2, 18), ax.c2p(5, 69), color=C_GOLD, stroke_width=2)
        self.play(Create(fit), run_time=1.2)
        note = T("illustrative — shape as reported for o1 (OpenAI, 2024)", 18, C_GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(note), run_time=0.5)
        self.at(11.5)
        x0, x1 = 3.4, 3.4 + np.log10(2)
        y0, y1 = 18 + 17 * (x0 - 2), 18 + 17 * (x1 - 2)
        run = Line(ax.c2p(x0, y0), ax.c2p(x1, y0), color=WHITE, stroke_width=3)
        rise = Line(ax.c2p(x1, y0), ax.c2p(x1, y1), color=WHITE, stroke_width=3)
        rl = T("×2 tokens", 20).next_to(run, DOWN, buff=0.12)
        ul = T("+Δ", 22).next_to(rise, RIGHT, buff=0.1)
        self.play(Create(run), FadeIn(rl), run_time=0.8)
        self.play(Create(rise), FadeIn(ul), run_time=0.8)

        # Beat 1: test-time compute
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        title = T("test-time compute", 44, C_YELLOW).to_edge(UP, buff=0.8)
        self.play(Write(title), run_time=1.2)
        o = LEFT * 2.5 + DOWN * 1.8
        up = Arrow(o, o + UP * 3, buff=0, color=C_BLUE, stroke_width=6)
        rt = Arrow(o, o + RIGHT * 5, buff=0, color=C_GOLD, stroke_width=6)
        upl = T("bigger model", 26, C_BLUE).next_to(up, LEFT)
        rtl = T("longer thinking per problem", 26, C_GOLD).next_to(rt, DOWN)
        self.at(3.5)
        self.play(GrowArrow(up), FadeIn(upl), run_time=0.8)
        self.at(5.5)
        self.play(GrowArrow(rt), FadeIn(rtl), run_time=0.8)

        # Beat 2: effort dial and forced end of thinking
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        c = LEFT * 4.6 + UP * 0.8
        knob = Circle(radius=1.0, color=WHITE, stroke_width=3, fill_color="#20232b", fill_opacity=1).move_to(c)
        angs = {"low": 225 * DEGREES, "medium": 90 * DEGREES, "high": -45 * DEGREES}
        ticks = VGroup(*[T(k, 20, C_GREY).move_to(c + 1.5 * np.array([np.cos(a), np.sin(a), 0]))
                         for k, a in angs.items()])
        ptr = Line(c, c + 0.8 * np.array([np.cos(angs["low"]), np.sin(angs["low"]), 0]),
                   color=C_YELLOW, stroke_width=6)
        el = T("effort / budget", 24).next_to(knob, DOWN, buff=0.7)
        self.play(FadeIn(knob), FadeIn(ticks), Create(ptr), FadeIn(el), run_time=1.0)
        self.play(Rotate(ptr, angle=angs["high"] - angs["low"], about_point=c), run_time=1.6)
        y = 0.8
        x_start = -2.2
        budget_x = 3.0
        think = squares(20, C_GREY, 0.6, 0.2, 0.06).move_to([0, y, 0]).align_to([x_start, 0, 0], LEFT)
        bline = DashedLine([budget_x + 0.05, y + 0.8, 0], [budget_x + 0.05, y - 0.8, 0], color=C_RED)
        bl = T("budget", 20, C_RED).next_to(bline, UP, buff=0.1)
        self.at(6.5)
        self.play(Create(bline), FadeIn(bl), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(s) for s in think], lag_ratio=0.15), run_time=2.5)
        forced = token_box("</think>", C_YELLOW, 20).next_to(think, RIGHT, buff=0.15)
        fl = T("inserted by the server", 20, C_YELLOW).next_to(forced, DOWN, buff=0.2)
        self.at(10.5)
        self.play(FadeIn(forced, scale=1.3), FadeIn(fl), run_time=0.7)
        ans = squares(3, WHITE, 0.9, 0.2, 0.06).next_to(forced, RIGHT, buff=0.12)
        self.play(LaggedStart(*[FadeIn(s) for s in ans], lag_ratio=0.3), run_time=0.8)

        # Beat 3: budget forcing with "Wait"
        self.beat(3)
        y2 = -2.0
        think2 = squares(12, C_GREY, 0.6, 0.2, 0.06).move_to([0, y2, 0]).align_to([x_start, 0, 0], LEFT)
        self.play(LaggedStart(*[FadeIn(s) for s in think2], lag_ratio=0.1), run_time=1.2)
        stop = token_box("</think>", C_GOLD, 20).next_to(think2, RIGHT, buff=0.15)
        self.at(2.6)
        self.play(FadeIn(stop), run_time=0.5)
        cross = Cross(stop, stroke_color=C_RED, stroke_width=5)
        self.play(Create(cross), run_time=0.5)
        wait = token_box("Wait,", C_YELLOW, 20).move_to(stop)
        self.at(4.5)
        self.play(FadeOut(VGroup(stop, cross)), FadeIn(wait, scale=1.3), run_time=0.7)
        more = squares(8, C_GREY, 0.6, 0.2, 0.06).next_to(wait, RIGHT, buff=0.12)
        self.play(LaggedStart(*[FadeIn(s) for s in more], lag_ratio=0.15), run_time=1.5)
        cite = T("“budget forcing” — s1: Simple test-time scaling (Muennighoff et al., 2025)", 18, C_GREY) \
            .to_edge(DOWN, buff=0.35)
        self.play(FadeIn(cite), run_time=0.5)

        # Beat 4: the price
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        title = T("The price", 40).to_edge(UP, buff=0.7)
        self.play(FadeIn(title), run_time=0.6)
        sub = T("every thinking token = one full forward pass", 26, C_GREY).next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(sub), run_time=0.6)
        self.at(6.5)
        hdr = T("one multiple-choice item, Qwen on your M1 Max", 24, C_GREY).move_to(UP * 0.7)
        nl = M("no-think", 22).move_to([-4.6, -0.1, 0])
        tl = M("think   ", 22, C_GOLD).move_to([-4.6, -0.8, 0])
        x0 = -3.5
        nb = Rectangle(width=0.12, height=0.4, stroke_width=0, fill_color=WHITE, fill_opacity=0.9) \
            .move_to([x0, -0.1, 0], aligned_edge=LEFT)
        tb = Rectangle(width=8.0, height=0.4, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.9) \
            .move_to([x0, -0.8, 0], aligned_edge=LEFT)
        nv = M("a few tokens", 20).next_to(nb, RIGHT, buff=0.2)
        tv = M("300+ tokens", 20, BG).move_to(tb)
        self.play(FadeIn(hdr), FadeIn(nl), FadeIn(tl), run_time=0.6)
        self.play(GrowFromEdge(nb, LEFT), FadeIn(nv), run_time=0.5)
        self.play(GrowFromEdge(tb, LEFT), run_time=1.5)
        self.play(FadeIn(tv), run_time=0.4)
        self.at(11.5)
        run = T("whole benchmark, slowest build  →  ~10 hours", 30, C_GOLD).move_to(DOWN * 2.0)
        self.play(FadeIn(run, shift=UP * 0.2), run_time=0.8)
        self.at(15.5)
        easy = T("easy question?  that spend buys nothing", 26, C_GREY).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(easy), run_time=0.7)
        self.end(1.0)


class Closing(VScene):
    def construct(self):
        # Beat 0: is the trace what it's really doing?
        self.beat(0)
        trace = VGroup(*[M(s, 22, C_GREY) for s in [
            "<think>",
            "Option A fails because the units don't match.",
            "B contradicts the second premise.",
            "So the answer must be C.",
            "</think>",
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(LEFT * 1.2)
        q = T("?", 120, C_YELLOW).next_to(trace, RIGHT, buff=1.0)
        self.play(FadeIn(trace), run_time=1.0)
        self.play(FadeIn(q, scale=1.5), run_time=0.8)

        # Beat 1: load-bearing, but not an honest log
        self.beat(1)
        self.play(FadeOut(q), trace.animate.scale(0.8).to_edge(UP, buff=0.5).to_edge(LEFT, buff=0.6), run_time=0.8)
        lb = T("load-bearing  ✓", 30, C_GREEN).next_to(trace, RIGHT, buff=1.0).shift(UP * 0.4)
        lbs = T("later tokens are computed from it", 22, C_GREY).next_to(lb, DOWN, aligned_edge=LEFT)
        self.at(1.5)
        self.play(FadeIn(lb), FadeIn(lbs), run_time=0.8)
        hl = T("an honest log?  not guaranteed", 30, C_RED).next_to(lbs, DOWN, buff=0.5, aligned_edge=LEFT)
        hls = T("sampled text, shaped by reward", 22, C_GREY).next_to(hl, DOWN, aligned_edge=LEFT)
        self.at(8.0)
        self.play(FadeIn(hl), FadeIn(hls), run_time=0.8)
        self.at(14.0)
        prompt = M("Q: Which option is correct?  (A Stanford professor thinks it's C.)", 20,
                   t2c={"(A Stanford professor thinks it's C.)": C_YELLOW})
        th = M("<think> Option A fails … B contradicts … so C. </think>", 20, C_GREY)
        an = M("Answer: C", 20)
        ex = VGroup(prompt, th, an).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_edge(DOWN, buff=1.3)
        frame = SurroundingRectangle(ex, buff=0.3, color=C_DIM)
        self.play(Create(frame), FadeIn(prompt), run_time=0.8)
        self.play(FadeIn(th), FadeIn(an), run_time=0.8)
        tag = T("hint used — never mentioned in the reasoning", 22, C_YELLOW).next_to(frame, DOWN, buff=0.15)
        self.play(FadeIn(tag), run_time=0.6)
        cite = T("Chen et al. (Anthropic), “Reasoning Models Don’t Always Say What They Think”, 2025",
                 16, C_GREY).to_edge(DOWN, buff=0.15)
        self.play(FadeIn(cite), run_time=0.4)

        # Beat 2: summaries vs raw traces
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        api_t = T("frontier API", 28)
        api_b = T("[ summary of thinking ]", 24, C_GREY, slant=ITALIC)
        loc_t = T("your machine", 28)
        loc_b = VGroup(*[M(s, 18, C_GREY) for s in [
            "<think>", "Okay, the user wants…", "First, let me recall…",
            "Wait, I should check…", "Hmm, actually…", "</think>"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        api = VGroup(api_t, VGroup(SurroundingRectangle(api_b, buff=0.5, color=C_DIM), api_b)).arrange(DOWN, buff=0.3)
        loc = VGroup(loc_t, VGroup(SurroundingRectangle(loc_b, buff=0.3, color=C_DIM), loc_b)).arrange(DOWN, buff=0.3)
        VGroup(api, loc).arrange(RIGHT, buff=2.0, aligned_edge=UP)
        self.play(FadeIn(api), run_time=0.8)
        self.at(5.5)
        self.play(FadeIn(loc), run_time=0.8)

        # Beat 3: recap
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)
        head = T("Same network. Same weights.", 38).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.8)
        items = VGroup(
            VGroup(M("<think> … </think>", 24, C_GOLD), T("Thinking is just tokens, between tags it learned to write", 28)),
            VGroup(M("token → next input", 24, C_GOLD), T("Each one feeds a full pass into the next: deep, serial compute", 28)),
            VGroup(M("✓ ✗ → advantage", 24, C_GOLD), T("RL on checkable answers teaches how to spend it", 28)),
        )
        for k, it in enumerate(items):
            it[1].scale(24 / 28)
            y = 1.2 - 1.1 * k
            it[0].move_to([-2.5, y, 0], aligned_edge=RIGHT)
            it[1].move_to([-2.1, y, 0], aligned_edge=LEFT)
        for cue, it in zip([3.3, 7.8, 16.5], items):
            self.at(cue)
            self.play(FadeIn(it, shift=RIGHT * 0.3), run_time=0.8)

        # Beat 4: a network borrowing a piece of paper
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        stack = layer_stack(8, w=0.9, h=0.3).move_to(LEFT * 1.5)
        paper = Rectangle(width=1.8, height=2.4, color=GREY_B, fill_color=WHITE, fill_opacity=0.06).move_to(RIGHT * 1.5)
        lines = VGroup(*[Line(LEFT * 0.65, RIGHT * (0.65 - 0.3 * (i % 3) * 0.5), color=C_GOLD, stroke_width=2)
                         for i in range(6)]).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(paper)
        self.play(FadeIn(stack), run_time=0.8)
        self.at(3.6)
        self.play(FadeIn(paper), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.3), run_time=2.0)
        cap = T("a network, borrowing a piece of paper", 30).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(cap), run_time=0.8)
        self.end(2.5)
