from common import *


class Intro(VScene):
    def construct(self):
        # Beat 0: a model thinking before it answers
        self.beat(0)
        q = T("What is 37 × 46?", 34)
        bubble = SurroundingRectangle(q, buff=0.25, corner_radius=0.2, stroke_color=C_BLUE,
                                      fill_color=C_BLUE, fill_opacity=0.12)
        user = VGroup(bubble, q).to_edge(UP, buff=0.8).shift(RIGHT * 2.5)
        self.play(FadeIn(user, shift=DOWN * 0.3), run_time=1)

        head = T("Thinking…", 26, C_GREY, slant=ITALIC)
        lines = VGroup(*[M(s, 22, C_GREY) for s in [
            "37 × 46 = 37 × 40 + 37 × 6",
            "37 × 40 = 1480",
            "37 × 6 = 222",
            "1480 + 222 = 1702",
            "Check: 50 × 37 − 4 × 37 = 1850 − 148 = 1702 ✓",
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        trace = VGroup(head, lines).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        trace.next_to(user, DOWN, buff=0.6).to_edge(LEFT, buff=1.2)
        bar = Line(trace.get_corner(UL) + LEFT * 0.25, trace.get_corner(DL) + LEFT * 0.25,
                   color=C_DIM, stroke_width=4)
        self.play(FadeIn(head), Create(bar), run_time=0.8)
        for ln in lines:
            self.play(AddTextLetterByLetter(ln), run_time=1.0)
        ans = T("1702", 44).next_to(trace, DOWN, buff=0.5).align_to(trace, LEFT)
        self.play(FadeIn(ans, scale=1.2), run_time=0.8)

        # Beat 1: same weights, it just writes more
        self.beat(1)
        self.play(FadeOut(VGroup(user, trace, bar, ans)), run_time=0.8)
        off = layer_stack(6).move_to(LEFT * 3.5 + UP * 1.2)
        on = layer_stack(6).move_to(RIGHT * 3.5 + UP * 1.2)
        off_l = T("thinking off", 28, C_GREY).next_to(off, UP)
        on_l = T("thinking on", 28, C_GOLD).next_to(on, UP)
        eq = T("=", 64).move_to((off.get_center() + on.get_center()) / 2)
        self.play(FadeIn(off), FadeIn(on), FadeIn(off_l), FadeIn(on_l), run_time=1)
        self.play(Write(eq), run_time=0.6)
        same = VGroup(T("same weights", 28), T("same architecture", 28), T("same file on disk", 28)) \
            .arrange(DOWN, buff=0.15).next_to(eq, DOWN, buff=0.6)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in same], lag_ratio=0.6), run_time=2.4)

        def squares(n, color, op=0.6):
            return VGroup(*[Square(0.17, stroke_width=0, fill_color=color, fill_opacity=op)
                            for _ in range(n)]).arrange(RIGHT, buff=0.05)
        off_tokens = squares(4, WHITE, 0.9).next_to(off, DOWN, buff=1.9)
        on_think = squares(36, C_GREY, 0.5).arrange_in_grid(rows=3, buff=0.05)
        on_tokens = VGroup(on_think, squares(4, WHITE, 0.9)).arrange(RIGHT, buff=0.15, aligned_edge=DOWN)
        on_tokens.next_to(on, DOWN, buff=1.7)
        self.play(FadeOut(same), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(s) for s in off_tokens], lag_ratio=0.3), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(s) for s in on_think], lag_ratio=0.1),
                  run_time=min(3.5, self.left()))
        self.play(LaggedStart(*[FadeIn(s) for s in on_tokens[1]], lag_ratio=0.3), run_time=0.8)
        more = T("…it just writes more", 28, C_GOLD).next_to(on_tokens, DOWN, buff=0.35)
        self.play(FadeIn(more), run_time=0.6)

        # Beat 2: the three questions
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        title = T("How can writing more make a model smarter?", 40).to_edge(UP, buff=1.0)
        self.play(Write(title), run_time=1.8)
        items = VGroup(
            T("1.  What thinking is, mechanically", 34),
            T("2.  Why extra tokens buy capability", 34),
            T("3.  How a model learns to use them", 34),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.55).next_to(title, DOWN, buff=1.0)
        cues = [4.6, 7.6, 10.4]  # seconds into the clip where each idea is spoken
        start = self._beat_end - DURATIONS["Intro_2"]
        for item, cue in zip(items, cues):
            wait = start + cue - self.renderer.time
            if wait > 0:
                self.wait(wait)
            self.play(FadeIn(item, shift=RIGHT * 0.3), run_time=0.7)
        self.end(1.5)


SPECIAL = {"<|im_start|>": C_PURPLE, "<|im_end|>": C_PURPLE, "<think>": C_GOLD, "</think>": C_GOLD}


def code_line(s, size=26, color=WHITE):
    return M(s, size, color, t2c=SPECIAL)


class JustTokens(VScene):
    def construct(self):
        # Beat 0: the chat template
        self.beat(0)
        head = T("Every chat is one long string of tokens", 36).to_edge(UP, buff=0.6)
        self.play(FadeIn(head), run_time=0.8)
        prompt = VGroup(
            code_line("<|im_start|>user"),
            code_line("What is 37 × 46?<|im_end|>"),
            code_line("<|im_start|>assistant"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_edge(LEFT, buff=1.0).shift(UP * 1.6)
        for ln in prompt:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.8)
        cursor = Rectangle(width=0.15, height=0.35, stroke_width=0, fill_color=WHITE, fill_opacity=0.9)
        cursor.next_to(prompt, DOWN, buff=0.2).align_to(prompt, LEFT)
        note = T("model continues from here", 26, C_YELLOW).next_to(cursor, RIGHT, buff=0.6)
        arr = Arrow(note.get_left(), cursor.get_right(), buff=0.1, color=C_YELLOW, stroke_width=3)
        self.play(FadeIn(cursor), GrowArrow(arr), FadeIn(note), run_time=1)
        self.play(cursor.animate.set_opacity(0), run_time=0.4)
        self.play(cursor.animate.set_opacity(0.9), run_time=0.4)

        # Beat 1: the model writes a think block, then the answer
        self.beat(1)
        self.play(FadeOut(arr), FadeOut(note), FadeOut(cursor), run_time=0.5)
        reply = VGroup(
            code_line("<think>"),
            code_line("37 × 46 = 37×40 + 37×6", color=C_GREY),
            code_line("        = 1480 + 222 = 1702", color=C_GREY),
            code_line("</think>"),
            code_line("The answer is 1702.<|im_end|>"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(prompt, DOWN, buff=0.2).align_to(prompt, LEFT)
        self.wait(1.5)
        self.play(AddTextLetterByLetter(reply[0]), run_time=0.8)
        self.play(AddTextLetterByLetter(reply[1]), run_time=1.6)
        self.play(AddTextLetterByLetter(reply[2]), run_time=1.6)
        self.wait(1.0)
        self.play(AddTextLetterByLetter(reply[3]), run_time=0.8)
        self.play(AddTextLetterByLetter(reply[4]), run_time=1.6)

        # Beat 2: server splits on the tags
        self.beat(2)
        think = VGroup(*reply[0:4])
        b1 = Brace(think, RIGHT, color=C_GOLD)
        l1 = M('"reasoning_content"', 24, C_GOLD).next_to(b1, RIGHT)
        b2 = Brace(reply[4], RIGHT, color=WHITE)
        l2 = M('"content"', 24).next_to(b2, RIGHT)
        self.wait(1.0)
        self.play(think.animate.set_opacity(1), Indicate(reply[0], color=C_GOLD),
                  Indicate(reply[3], color=C_GOLD), run_time=1.5)
        self.wait(1.5)
        self.play(GrowFromCenter(b1), FadeIn(l1, shift=LEFT * 0.2), run_time=1)
        self.play(GrowFromCenter(b2), FadeIn(l2, shift=LEFT * 0.2), run_time=1)
        sub = T("no separate engine — the server splits the text on the tags", 26, C_GREY) \
            .to_edge(DOWN, buff=0.6)
        self.play(FadeIn(sub), run_time=0.8)

        # Beat 3: the empty-think prefill trick
        self.beat(3)
        self.play(FadeOut(VGroup(reply, b1, l1, b2, l2, sub)), run_time=0.7)
        new_head = T("The empty-think prefill", 36).to_edge(UP, buff=0.6)
        self.play(Transform(head, new_head), run_time=0.8)
        pre = VGroup(code_line("<think>"), code_line("</think>")) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(prompt, DOWN, buff=0.2).align_to(prompt, LEFT)
        self.wait(2.5)
        self.play(FadeIn(pre[0]), run_time=0.5)
        self.play(FadeIn(pre[1]), run_time=0.5)
        box = SurroundingRectangle(pre, color=C_YELLOW, buff=0.12)
        you = T("you wrote this", 26, C_YELLOW).next_to(box, RIGHT, buff=0.4)
        self.play(Create(box), FadeIn(you), run_time=0.8)
        self.wait(2.0)
        over = T("…as far as the model can tell, thinking is over", 26, C_GREY).next_to(box, DOWN, buff=1.2).align_to(box, LEFT)
        self.play(FadeIn(over), run_time=0.8)
        ans = code_line("The answer is 1702.<|im_end|>").next_to(pre, DOWN, buff=0.2).align_to(pre, LEFT)
        self.wait(1.5)
        self.play(AddTextLetterByLetter(ans), run_time=1.6)

        # Beat 4: Qwen3's non-thinking mode is exactly this
        self.beat(4)
        self.play(FadeOut(VGroup(prompt, pre, box, you, over, ans)), run_time=0.7)
        new_head = T("Qwen3 chat template, enable_thinking=False", 34).to_edge(UP, buff=0.6)
        self.play(Transform(head, new_head), run_time=0.8)
        tmpl = VGroup(
            code_line("<|im_start|>assistant"),
            code_line("<think>"),
            code_line("</think>"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 0.6)
        tmpl[2].shift(DOWN * 0.4)
        self.play(FadeIn(tmpl, shift=UP * 0.2), run_time=1)
        self.play(Circumscribe(VGroup(tmpl[1], tmpl[2]), color=C_YELLOW), run_time=1.5)
        self.wait(2.0)
        punch = T("Thinking is a learned convention,", 36)
        punch2 = T("not a switch in the hardware.", 36, C_YELLOW)
        pg = VGroup(punch, punch2).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(punch), run_time=0.8)
        self.play(FadeIn(punch2), run_time=0.8)
        self.end(1.5)


class SerialDepth(VScene):
    L = 5
    SP = 1.15

    def column(self, x, color=C_BLUE):
        col = layer_stack(self.L, color=color)
        col.move_to([x, 0.1, 0])
        return col

    def construct(self):
        L, SP = self.L, self.SP
        prompt_toks = ["What", "is", "37", "×", "46", "?"]
        gen_toks = ["37×40", "1480", "222", "1702"]
        n_total = len(prompt_toks) + len(gen_toks)
        xs = [(i - (n_total - 1) / 2) * SP for i in range(n_total)]
        offset = -(xs[len(prompt_toks) - 1] + xs[0]) / 2  # centre the prompt columns at first

        # Beat 0: columns of layers, attention looks back
        self.beat(0)
        cols = VGroup(*[self.column(xs[i] + offset) for i in range(len(prompt_toks))])
        toks = VGroup(*[M(t, 22).next_to(c, DOWN, buff=0.35) for t, c in zip(prompt_toks, cols)])
        last = len(prompt_toks) - 1
        self.play(FadeIn(cols[last]), FadeIn(toks[last]), run_time=1)
        up = Arrow(toks[last].get_top(), cols[last].get_top() + UP * 0.6, buff=0.05,
                   color=C_YELLOW, stroke_width=4).set_opacity(0.0)
        self.play(LaggedStart(*[Indicate(r, color=C_YELLOW, scale_factor=1.1) for r in cols[last]],
                              lag_ratio=0.35), run_time=2.0)
        self.wait(0.8)
        self.play(LaggedStart(*[FadeIn(VGroup(c, t)) for c, t in zip(cols[:last], toks[:last])],
                              lag_ratio=0.15), run_time=1.5)
        att = VGroup()
        for layer in range(1, L):
            for j in range(last):
                att.add(Line(cols[j][layer - 1].get_right(), cols[last][layer].get_left(),
                             stroke_width=1.2, color=C_TEAL, stroke_opacity=0.45))
        self.wait(1.5)
        self.play(LaggedStart(*[Create(a) for a in att], lag_ratio=0.03), run_time=2.5)
        att_l = T("attention: look back at earlier positions", 24, C_TEAL).to_edge(UP, buff=0.5)
        self.play(FadeIn(att_l), run_time=0.7)

        # Beat 1: fixed height
        self.beat(1)
        self.play(FadeOut(att), FadeOut(att_l), run_time=0.6)
        brace = Brace(cols[0], LEFT, color=C_YELLOW)
        bl = VGroup(T("fixed height", 26, C_YELLOW), T("(e.g. 64 layers)", 22, C_GREY)) \
            .arrange(DOWN, aligned_edge=RIGHT, buff=0.1).next_to(brace, LEFT)
        self.play(GrowFromCenter(brace), FadeIn(bl), run_time=1.0)
        self.wait(3.0)
        per = T("64 layers of computation per token. No more.", 30).to_edge(UP, buff=0.5)
        self.play(FadeIn(per), run_time=0.8)
        self.wait(2.5)
        easy = T("“2 + 2”  →  64 layers", 26, C_GREY)
        hard = T("“a hard proof”  →  64 layers", 26, C_GREY)
        VGroup(easy, hard).arrange(DOWN, buff=0.15).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(easy), run_time=0.6)
        self.play(FadeIn(hard), run_time=0.6)

        # Beat 2: answering immediately = one trip up the stack
        self.beat(2)
        self.play(FadeOut(VGroup(easy, hard, per)), run_time=0.5)
        path = Line(cols[last].get_bottom() + DOWN * 0.1, cols[last].get_top() + UP * 0.1,
                    color=C_YELLOW, stroke_width=7)
        out = M("1702?", 24, C_RED).next_to(cols[last], UP, buff=0.3)
        self.play(Create(path), run_time=1.5)
        self.play(FadeIn(out, shift=UP * 0.2), run_time=0.6)
        steps = T("serial steps available:  L", 30, C_YELLOW).to_edge(UP, buff=0.5)
        self.play(FadeIn(steps), run_time=0.7)

        # Beat 3: the output token feeds back as the next input
        self.beat(3)
        self.play(FadeOut(out), FadeOut(path), FadeOut(steps), FadeOut(brace), FadeOut(bl), run_time=0.6)
        self.play(VGroup(cols, toks).animate.shift(LEFT * offset), run_time=1.0)
        top_y = cols[0].get_top()[1]
        bot_y = toks[0].get_center()[1]

        def feedback(k, text):
            """Output at top of column k loops round to become input of column k+1."""
            x0, x1 = xs[k], xs[k + 1]
            xm = (x0 + x1) / 2
            start = np.array([x0, top_y + 0.35, 0])
            end = np.array([x1, bot_y, 0])
            curve = CubicBezier(start, [xm + 0.1, top_y + 0.9, 0], [xm - 0.1, bot_y - 0.9, 0], end)
            tok = M(text, 20, C_GOLD).move_to(start)
            return curve, tok

        new_cols, new_toks, curves = VGroup(), VGroup(), VGroup()
        for i, text in enumerate(gen_toks):
            k = last + i
            curve, tok = feedback(k, text)
            col = self.column(xs[k + 1], color=C_GOLD)
            rt = 1.4 if i == 0 else 0.9
            self.play(FadeIn(tok, shift=UP * 0.2), run_time=0.4)
            dashed = DashedVMobject(curve, num_dashes=30).set_color(C_GOLD).set_stroke(width=2)
            self.play(Create(dashed), MoveAlongPath(tok, curve), run_time=rt)
            self.play(FadeIn(col), run_time=0.4)
            new_cols.add(col)
            new_toks.add(tok)
            curves.add(dashed)
            if i == 0:
                self.wait(1.5)

        # Beat 4: depth multiplies; tokens are a scratchpad
        self.beat(4)
        pts = [np.array([xs[last], bot_y + 0.3, 0]), np.array([xs[last], top_y + 0.1, 0])]
        for i in range(len(gen_toks)):
            k = last + i
            pts += [np.array([(xs[k] + xs[k + 1]) / 2, top_y + 0.1, 0]),
                    np.array([(xs[k] + xs[k + 1]) / 2, bot_y + 0.3, 0]),
                    np.array([xs[k + 1], bot_y + 0.3, 0]),
                    np.array([xs[k + 1], top_y + 0.1, 0])]
        snake = VMobject(color=C_YELLOW, stroke_width=6).set_points_as_corners(pts)
        self.wait(2.5)
        self.play(Create(snake), run_time=4.0, rate_func=linear)
        depth = T("serial depth:  L × N", 32, C_YELLOW).to_edge(UP, buff=0.4)
        self.play(FadeIn(depth), run_time=0.7)
        sb = Brace(new_toks, DOWN, color=C_GOLD)
        sl = T("scratchpad", 28, C_GOLD).next_to(sb, DOWN, buff=0.1)
        self.wait(2.0)
        self.play(GrowFromCenter(sb), FadeIn(sl), run_time=1.0)

        # Beat 5: head vs paper
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        head_t = T("in your head", 32, C_GREY)
        head_q = M("37 × 46 = ?", 34)
        head = VGroup(head_t, head_q).arrange(DOWN, buff=0.8).move_to(LEFT * 3.5 + UP * 0.6)
        paper_t = T("on paper", 32, C_GREY)
        work = VGroup(*[M(s, 30) for s in ["   37", " × 46", " ────", "  222", " 1480", " ────", " 1702"]]) \
            .arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        sheet = SurroundingRectangle(work, buff=0.35, color=GREY_B, fill_color=WHITE, fill_opacity=0.05)
        paper = VGroup(paper_t, VGroup(sheet, work)).arrange(DOWN, buff=0.4).move_to(RIGHT * 3.5)
        paper_t.align_to(head_t, UP)
        self.play(FadeIn(head_t), FadeIn(head_q), run_time=0.8)
        self.wait(1.5)
        self.play(FadeIn(paper_t), Create(sheet), run_time=0.8)
        for w in work:
            self.play(FadeIn(w, shift=DOWN * 0.1), run_time=0.45)
        self.wait(1.0)
        same = T("same brain — just somewhere to put intermediate results", 26, C_YELLOW).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(same), run_time=0.8)

        # Beat 6: the theory
        self.beat(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        big = Circle(radius=0.9, color=C_GOLD, fill_opacity=0.08).move_to(DOWN * 0.3)
        small = Circle(radius=0.9, color=C_BLUE, fill_opacity=0.2).move_to(big.get_center())
        sl = T("answer in\none step", 24, C_BLUE).move_to(small)
        self.play(GrowFromCenter(small), FadeIn(sl), run_time=1.2)
        self.wait(2.5)
        n = ValueTracker(0)
        label = always_redraw(lambda: T(f"with {int(n.get_value())} chain-of-thought steps", 28, C_GOLD)
                              .to_edge(UP, buff=0.5))
        self.add(big, label)
        self.bring_to_front(small, sl)
        big.add_updater(lambda m: m.set(width=2 * (0.9 + 0.0095 * n.get_value()))
                        .move_to(small.get_center()))
        self.play(n.animate.set_value(200), run_time=5, rate_func=smooth)
        big.clear_updaters()
        cite = T("Merrill & Sabharwal, “The Expressive Power of Transformers with Chain of Thought” (2024)",
                 18, C_GREY).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(cite), run_time=0.6)
        self.end(1.5)
