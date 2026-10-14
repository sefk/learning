from kit.scene import *

from data import MATH, MEASURED
from scenes_a import bar

KIB = 1024


class KVCache(VScene):
    def construct(self):
        moe, dense = MATH["moe"], MATH["dense"]

        # Beat 0: it lives next to the weights and grows
        self.beat(0)
        mem = Rectangle(width=11, height=0.8, stroke_color=C_GREY, stroke_width=1.5).move_to(DOWN * 0.2)
        ml = T("64 GB unified memory", 22, C_GREY).next_to(mem, UP, buff=0.15).align_to(mem, LEFT)
        w = Rectangle(width=11 * 19.5 / 64, height=0.8, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.7) \
            .align_to(mem, LEFT).match_y(mem)
        wl = T("weights 19.5 GB", 20).move_to(w)
        self.play(Create(mem), FadeIn(ml), FadeIn(w), FadeIn(wl), run_time=0.8)
        cache = Rectangle(width=0.01, height=0.8, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.8) \
            .next_to(w, RIGHT, buff=0)
        self.add(cache)
        self.cue("And it grows")
        grown = Rectangle(width=11 * 5.4 / 64, height=0.8, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.8) \
            .next_to(w, RIGHT, buff=0)
        cl = T("KV cache", 20, C_YELLOW).next_to(grown, DOWN, buff=0.15)
        self.play(Transform(cache, grown), FadeIn(cl), run_time=2.5, rate_func=linear)

        # Beat 1: two kilobytes per layer per token
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        eq = VGroup(T("2 shared heads", 32), T("×", 32, C_GREY), T("256 numbers", 32), T("×", 32, C_GREY),
                    T("2 bytes", 32), T("×", 32, C_GREY), T("(K + V)", 32)).arrange(RIGHT, buff=0.2)
        res = T("= 2 KB per attention layer, per token", 36, C_YELLOW)
        VGroup(eq, res).arrange(DOWN, buff=0.5)
        self.cue("each attention layer stores")
        self.play(Write(eq), run_time=2.5)
        self.cue("That's two kilobytes")
        self.play(FadeIn(res, shift=UP * 0.2), run_time=0.8)

        # Beat 2: 20 KB per token; vs Qwen3-30B-A3B
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        title = T("KV cache per token", 28, C_GREY).to_edge(UP, buff=0.5)
        q3 = 48 * 2 * 4 * 128 * 2  # Qwen3-30B-A3B: 48 full-attention layers, 4 KV heads of 128
        rows = [("Qwen3.6-35B-A3B", moe["kv_bytes_per_token"], C_GOLD),
                ("Qwen3.6-27B", dense["kv_bytes_per_token"], C_BLUE),
                ("Qwen3-30B-A3B (2025)", q3, C_GREY)]
        bars = VGroup()
        for i, (name, v, c) in enumerate(rows):
            b = bar(v, q3, 8, c).move_to([0, 1.2 - i * 1.0, 0]).align_to(LEFT * 2.5, LEFT)
            lab = T(name, 24, c).next_to(b, LEFT, buff=0.25)
            val = T(f"{v / KIB:.0f} KB", 24, c).next_to(b, RIGHT, buff=0.2)
            bars.add(VGroup(b, lab, val))
        only = T("only 10 of the 40 layers keep one", 22, C_GREY).next_to(title, DOWN, buff=0.15)
        self.play(FadeIn(title), FadeIn(only), run_time=0.6)
        self.cue("So your mixture")
        self.play(GrowFromEdge(bars[0][0], LEFT), FadeIn(bars[0][1]), FadeIn(bars[0][2]), run_time=0.8)
        self.cue("At its full window")
        full = T(f"× 262,144 tokens = {moe['kv_gb_at_262k']} GB", 28, C_GOLD).move_to(DOWN * 2.0)
        self.play(FadeIn(full), run_time=0.7)
        self.cue("Qwen three's thirty B")
        self.play(GrowFromEdge(bars[2][0], LEFT), FadeIn(bars[2][1]), FadeIn(bars[2][2]), run_time=0.8)

        # Beat 3: the dense model
        self.beat(3)
        self.play(GrowFromEdge(bars[1][0], LEFT), FadeIn(bars[1][1]), FadeIn(bars[1][2]), run_time=0.8)
        self.cue("At full length")
        dfull = T(f"dense at full length: {dense['kv_gb_at_262k']} GB of cache, more than its weights", 26, C_BLUE) \
            .move_to(DOWN * 2.6)
        self.play(FadeIn(dfull), run_time=0.7)

        # Beat 4: decode reads the cache too
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        ax = Axes(x_range=[0, 262144, 65536], y_range=[0, 8, 2], x_length=9, y_length=4.2, tips=False,
                  axis_config={"color": C_GREY, "include_ticks": False}).move_to(DOWN * 0.3)
        xl = T("context length →  262k", 22, C_GREY).next_to(ax.x_axis, DOWN, buff=0.2)
        yl = T("GB read per new token", 22, C_GREY).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=0.8)
        w_gb = moe["gb_read_per_token_4bit"]
        weights = ax.plot(lambda x: w_gb, color=C_GOLD, stroke_width=3)
        total = ax.plot(lambda x: w_gb + x * moe["kv_bytes_per_token"] / 1e9, color=C_YELLOW, stroke_width=3)
        wl = T(f"active weights {w_gb} GB", 22, C_GOLD).next_to(ax.c2p(150000, w_gb), DOWN, buff=0.15)
        self.cue("Every new token")
        self.play(Create(weights), FadeIn(wl), run_time=0.8)
        self.play(Create(total), run_time=1.5)
        tl = T("+ KV cache", 22, C_YELLOW).next_to(ax.c2p(200000, w_gb + 200000 * 20480 / 1e9), UP, buff=0.2)
        self.play(FadeIn(tl), run_time=0.4)
        self.cue("the cache is three times")
        end = Dot(ax.c2p(262144, w_gb + moe["kv_gb_at_262k"]), color=C_YELLOW)
        el = T(f"{w_gb + moe['kv_gb_at_262k']:.1f} GB per token", 22, C_YELLOW).next_to(end, LEFT, buff=0.2)
        self.play(FadeIn(end), FadeIn(el), run_time=0.6)
        self.end()


class Caching(VScene):
    def construct(self):
        # Beat 0: prefix reuse
        self.beat(0)
        prefix = Rectangle(width=6, height=0.6, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.6)
        r1 = VGroup(prefix.copy(), Rectangle(width=2, height=0.6, stroke_width=0, fill_color=C_GREY,
                                              fill_opacity=0.6)).arrange(RIGHT, buff=0)
        r2 = VGroup(prefix.copy(), Rectangle(width=2.6, height=0.6, stroke_width=0, fill_color=C_GOLD,
                                              fill_opacity=0.8)).arrange(RIGHT, buff=0)
        g = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to(UP * 0.5)
        l1 = T("request 1", 22, C_GREY).next_to(r1, LEFT, buff=0.3)
        l2 = T("request 2", 22, C_GREY).next_to(r2, LEFT, buff=0.3)
        self.play(FadeIn(r1), FadeIn(l1), run_time=0.8)
        self.cue("starts with exactly")
        self.play(FadeIn(r2), FadeIn(l2), run_time=0.8)
        same = T("same prefix: cache kept", 22, C_BLUE).next_to(r2[0], DOWN, buff=0.2)
        self.play(FadeIn(same), r2[0].animate.set_fill(opacity=0.25), run_time=0.8)
        self.cue("only prefills")
        new = T("only this is prefilled", 22, C_GOLD).next_to(r2[1], DOWN, buff=0.2)
        self.play(FadeIn(new), Indicate(r2[1], color=C_YELLOW), run_time=1.0)

        # Beat 1: the bench had to defeat it
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        b1 = bar(1, 11.6, 9, C_GREY).move_to(UP * 0.8).align_to(LEFT * 4, LEFT)
        b2 = bar(11.6, 11.6, 9, C_BLUE).move_to(DOWN * 0.2).align_to(LEFT * 4, LEFT)
        t1 = T("fresh prompt: prefill speed 1×", 22, C_GREY).next_to(b1, UP, buff=0.1).align_to(b1, LEFT)
        t2 = T("repeated prompt: prefill 11.6× faster", 22, C_BLUE).next_to(b2, UP, buff=0.1).align_to(b2, LEFT)
        self.play(GrowFromEdge(b1, LEFT), FadeIn(t1), run_time=0.6)
        self.cue("eleven point six")
        self.play(GrowFromEdge(b2, LEFT), FadeIn(t2), run_time=0.8)
        self.cue("So every prompt")
        nonce = VGroup(Rectangle(width=0.8, height=0.5, stroke_width=0, fill_color=C_RED, fill_opacity=0.8),
                       Rectangle(width=6, height=0.5, stroke_width=0, fill_color=C_GREY, fill_opacity=0.5)) \
            .arrange(RIGHT, buff=0).move_to(DOWN * 2.0)
        nl = T("random nonce first: no prefix ever matches", 22, C_RED).next_to(nonce, DOWN, buff=0.2)
        self.play(FadeIn(nonce), FadeIn(nl), run_time=0.8)

        # Beat 2: chat turns; editing invalidates
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        turns = VGroup(*[Rectangle(width=w, height=0.5, stroke_width=1, stroke_color=BG, fill_color=c,
                                   fill_opacity=0.7)
                         for w, c in [(1.6, C_GREY), (1.4, C_BLUE), (2.0, C_GOLD), (1.2, C_BLUE), (2.2, C_GOLD),
                                      (1.0, C_BLUE)]]).arrange(RIGHT, buff=0).move_to(UP * 0.8)
        tl = T("system · user · model · user · model · user", 20, C_GREY).next_to(turns, UP, buff=0.2)
        self.play(FadeIn(turns, lag_ratio=0.2), FadeIn(tl), run_time=1.2)
        self.cue("only the newest")
        self.play(turns[:-1].animate.set_fill(opacity=0.2), Indicate(turns[-1], color=C_YELLOW), run_time=1.0)
        self.cue("Edit an")
        edit = T("edit", 22, C_RED).next_to(turns[1], DOWN, buff=0.2)
        self.play(FadeIn(edit), turns[1:].animate.set_fill(C_RED, opacity=0.7), run_time=1.0)
        redo = T("everything after the edit is prefilled again", 22, C_RED).next_to(turns, DOWN, buff=0.8)
        self.play(FadeIn(redo), run_time=0.6)

        # Beat 3: KV can be trimmed; a DeltaNet state cannot
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        kv = VGroup(*[Rectangle(width=0.35, height=0.5, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8)
                      for _ in range(16)]).arrange(RIGHT, buff=0.04).move_to(UP * 1.4 + LEFT * 1.0)
        kvl = T("KV cache", 24, C_TEAL).next_to(kv, LEFT, buff=0.3)
        self.play(FadeIn(kv), FadeIn(kvl), run_time=0.6)
        self.cue("can be cut back")
        cut = DashedLine(UP * 0.4, DOWN * 0.4, color=C_YELLOW).move_to(kv[9].get_left() + LEFT * 0.02)
        self.play(Create(cut), kv[9:].animate.set_fill(opacity=0.15), run_time=0.8)
        st = Square(1.0, stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.8).move_to(DOWN * 1.0 + LEFT * 1.0)
        stl = T("DeltaNet state", 24, C_PURPLE).next_to(st, LEFT, buff=0.3)
        self.cue("A DeltaNet state")
        self.play(FadeIn(st), FadeIn(stl), run_time=0.6)
        x = Cross(st, stroke_color=C_RED, stroke_width=4)
        self.play(Create(x), run_time=0.6)
        self.cue("To rewind")
        snaps = VGroup(*[Square(0.4, stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.5) for _ in range(3)]) \
            .arrange(RIGHT, buff=0.2).next_to(st, RIGHT, buff=0.8)
        sl = T("saved checkpoints", 22, C_PURPLE).next_to(snaps, DOWN, buff=0.2)
        self.play(FadeIn(snaps, lag_ratio=0.3), FadeIn(sl), run_time=1.0)

        # Beat 4: API prompt caching
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        parts = VGroup(*[Rectangle(width=w, height=0.6, stroke_width=1, stroke_color=BG, fill_color=c,
                                   fill_opacity=0.75)
                         for w, c in [(2.6, C_GREY), (2.4, C_PURPLE), (4.0, C_BLUE), (1.2, C_GOLD)]]) \
            .arrange(RIGHT, buff=0).move_to(UP * 0.4)
        labels = VGroup(*[T(s, 20).move_to(p) for s, p in zip(["system prompt", "tools", "conversation", "new"],
                                                                parts)])
        self.play(FadeIn(parts), FadeIn(labels), run_time=0.8)
        brace = Brace(parts[:3], DOWN, color=C_YELLOW)
        bl = T("cached prefix: billed at a fraction", 24, C_YELLOW).next_to(brace, DOWN, buff=0.15)
        self.cue("a cached prefix")
        self.play(GrowFromCenter(brace), FadeIn(bl), run_time=0.8)
        self.cue("keep the system prompt")
        fixed = T("fixed, at the very front", 22, C_GREY).next_to(parts[:2], UP, buff=0.2)
        self.play(FadeIn(fixed), Indicate(parts[0]), Indicate(parts[1]), run_time=1.0)

        # Beat 5: when the window fills
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        win = Rectangle(width=10, height=0.6, stroke_color=C_GREY, stroke_width=1.5).move_to(UP * 2.0)
        fill = Rectangle(width=10, height=0.6, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.6).move_to(win)
        wl = T("context window", 22, C_GREY).next_to(win, UP, buff=0.15)
        self.play(Create(win), FadeIn(wl), run_time=0.5)
        self.play(GrowFromEdge(fill, LEFT), run_time=1.5)
        opts = VGroup(
            VGroup(T("drop the oldest turns", 26), T("truncation", 20, C_GREY)),
            VGroup(T("summarise, start fresh from the summary", 26), T("compaction (this video's session)", 20, C_GREY)),
            VGroup(T("fail quietly", 26), T("Apple's on-device model: empty answers past 4k", 20, C_GREY)),
        )
        for o in opts:
            o.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        opts.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(DOWN * 0.8)
        for phrase, o in zip(["drop the oldest", "Others compact", "some servers just fail"], opts):
            self.cue(phrase)
            self.play(FadeIn(o, shift=RIGHT * 0.2), run_time=0.7)
        self.end()


class Speculative(VScene):
    def construct(self):
        # Beat 0: one fetch, many uses
        self.beat(0)
        w = Square(0.6, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.85).move_to(LEFT * 4.5)
        wl = T("weights,\nfetched once", 22, C_GREY).next_to(w, DOWN, buff=0.2)
        self.play(FadeIn(w), FadeIn(wl), run_time=0.6)
        self.cue("using it for four")
        b1 = bar(1.0, 1.2, 6, C_BLUE).move_to(UP * 0.6).align_to(LEFT * 2.5, LEFT)
        b4 = bar(1.08, 1.2, 6, C_TEAL).move_to(DOWN * 0.4).align_to(LEFT * 2.5, LEFT)
        l1 = T("1 token", 22, C_BLUE).next_to(b1, RIGHT, buff=0.2)
        l4 = T("4 tokens: barely more", 22, C_TEAL).next_to(b4, RIGHT, buff=0.2)
        tl = T("time for one decode step (schematic)", 22, C_GREY).next_to(b1, UP, buff=0.3).align_to(b1, LEFT)
        self.play(FadeIn(tl), GrowFromEdge(b1, LEFT), FadeIn(l1), run_time=0.8)
        self.play(GrowFromEdge(b4, LEFT), FadeIn(l4), run_time=0.8)

        # Beat 1: draft, verify, accept
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        ctx = VGroup(*[token_box(s, WHITE, 22) for s in ["for", "i", "in"]]).arrange(RIGHT, buff=0.12)
        guess = VGroup(*[token_box(s, C_PURPLE, 22) for s in ["range", "(", "len", "("]]).arrange(RIGHT, buff=0.12)
        row = VGroup(ctx, guess).arrange(RIGHT, buff=0.3).move_to(UP * 1.6)
        self.play(FadeIn(ctx), run_time=0.5)
        self.cue("Something cheap")
        gl = T("cheap guesses", 22, C_PURPLE).next_to(guess, UP, buff=0.2)
        self.play(FadeIn(guess, lag_ratio=0.2), FadeIn(gl), run_time=1.0)
        self.cue("The big model then checks")
        big = RoundedRectangle(width=6, height=0.9, corner_radius=0.15, stroke_color=C_GOLD, fill_color=C_GOLD,
                               fill_opacity=0.15).move_to(DOWN * 1.0)
        bl = T("big model: one pass over all four", 24, C_GOLD).move_to(big)
        self.play(FadeIn(big), FadeIn(bl), run_time=0.8)
        self.cue("It keeps the guesses")
        verdicts = ["✓", "✓", "✓", "✗"]
        marks = VGroup(*[T(v, 28, C_GREEN if v == "✓" else C_RED).next_to(g, DOWN, buff=0.15)
                         for v, g in zip(verdicts, guess)])
        self.play(LaggedStart(*[FadeIn(m, scale=1.4) for m in marks], lag_ratio=0.2), run_time=1.0)
        fix = token_box("arr", C_GOLD, 22).next_to(guess[3], DOWN, buff=0.75)
        self.play(guess[3].animate.set_opacity(0.3), FadeIn(fix, shift=UP * 0.2), run_time=0.8)
        self.cue("The output is exactly")
        res = T("4 tokens from one pass of the big model, identical output", 24, C_YELLOW).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(res), run_time=0.7)

        # Beat 2: draft model or built-in MTP
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        a = VGroup(T("draft model", 30, C_PURPLE), T("a small model from the same family", 22, C_GREY)) \
            .arrange(DOWN, buff=0.15).move_to(LEFT * 3.2)
        b = VGroup(T("multi-token prediction", 30, C_GOLD), T("an extra layer inside the model", 22, C_GREY),
                   M("mtp_num_hidden_layers: 1", 20, C_GOLD)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.2)
        self.play(FadeIn(a), run_time=0.7)
        self.cue("Or it can be built in")
        self.play(FadeIn(b[:2]), run_time=0.7)
        self.cue("Your Qwen")
        self.play(FadeIn(b[2]), run_time=0.6)
        src = T("from your model's config.json", 20, C_GREY).next_to(b, DOWN, buff=0.2)
        self.play(FadeIn(src), run_time=0.4)

        # Beat 3: where it pays
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        good = VGroup(T("pays best", 28, C_GREEN), T("predictable text: code, boilerplate", 24)) \
            .arrange(DOWN, buff=0.15).move_to(UP * 1.0)
        self.play(FadeIn(good), run_time=0.7)
        self.cue("And it pays less")
        moe_note = VGroup(T("pays less on experts", 28, C_GOLD),
                          T("each guessed token may route to different experts", 24)) \
            .arrange(DOWN, buff=0.15).move_to(DOWN * 1.0)
        self.play(FadeIn(moe_note), run_time=0.7)
        self.end()


class Recap(VScene):
    def construct(self):
        # Beat 0: the formula
        self.beat(0)
        f = VGroup(T("tokens per second", 40), T("≈", 40, C_GREY), T("memory bandwidth", 40, C_BLUE),
                   T("÷", 40, C_GREY), T("bytes per token", 40, C_YELLOW)).arrange(RIGHT, buff=0.25)
        f.scale_to_fit_width(min(f.width, 12.5)).to_edge(UP, buff=0.7)
        self.play(Write(f), run_time=2.0)

        # Beat 1: the levers
        self.beat(1)
        moe = MATH["moe"]
        rows = VGroup(
            VGroup(T("mixture of experts", 28, C_GOLD),
                   T(f"{moe['params_total_b']:.0f} B → {moe['params_active_b']:.0f} B touched: "
                     f"{MEASURED['moe_decode'] / MEASURED['dense_decode']:.1f}× faster", 26)),
            VGroup(T("quantization", 28, C_PURPLE), T("4-bit costs nothing you can measure", 26)),
            VGroup(T("hybrid attention", 28, C_TEAL), T("20 KB per past token instead of ~100", 26)),
            VGroup(T("speculation", 28, C_GREEN), T("more tokens per weight read", 26)),
        )
        for r in rows:
            r.arrange(RIGHT, buff=0.5)
            r[0].align_to(LEFT * 5.8, LEFT)
            r[1].align_to(LEFT * 1.2, LEFT)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.75).move_to(DOWN * 0.4)
        for r in rows:
            r[1].shift(RIGHT * (-1.2 - r[1].get_left()[0]))
        for phrase, r in zip(["Mixture of experts cuts", "Quantization cuts", "Hybrid attention", "And speculation"],
                             rows):
            self.cue(phrase)
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.7)

        # Beat 2: the costs
        self.beat(2)
        costs = [T("all experts resident", 22, C_RED), T("too few bits: collapse", 22, C_RED),
                 T("lossy, can't rewind", 22, C_RED), T("helps experts less", 22, C_RED)]
        for c, r in zip(costs, rows):
            c.next_to(r, DOWN, buff=0.06).align_to(r[1], LEFT)
        for phrase, c in zip(["All the experts", "Too few bits", "Summarised attention", "And the dense"], costs):
            self.cue(phrase)
            self.play(FadeIn(c), run_time=0.5)
        code = T("…and the dense model still writes better code", 24, C_BLUE).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(code), run_time=0.5)

        # Beat 3: back to the start
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        last = T("for any one token, most of the model isn't there", 38, C_YELLOW)
        self.play(FadeIn(last, shift=UP * 0.2), run_time=1.2)
        self.end(tail=2.5)
