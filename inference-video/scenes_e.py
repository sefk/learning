from kit.scene import *

from data import MATH
from scenes_b import chip, layer_pattern, lever_list, speed_formula

WORDS = ["The", "keeper", "watched", "the", "boat", "until", "it"]
# illustrative attention weights for "it" (they add up to one)
WEIGHTS = [0.02, 0.10, 0.04, 0.02, 0.72, 0.10]


def sentence(y=1.6):
    return VGroup(*[token_box(w, WHITE, 22) for w in WORDS]).arrange(RIGHT, buff=0.18).move_to(UP * y)


def vec(n, color, cell=0.22, values=None, direction=RIGHT):
    """A vector drawn as a strip of cells; opacity follows |value|."""
    values = np.ones(n) * 0.8 if values is None else values
    return VGroup(*[Square(cell, stroke_width=0.5, stroke_color=BG, fill_color=color,
                           fill_opacity=0.15 + 0.8 * min(1, abs(v))) for v in values]).arrange(direction, buff=0)


def grid(values, color=C_PURPLE, cell=0.3):
    n = values.shape[0]
    g = VGroup(*[Square(cell, stroke_width=0.5, stroke_color=BG, fill_color=color,
                        fill_opacity=0.08 + 0.85 * min(1, abs(values[i, j])))
                 for i in range(n) for j in range(n)]).arrange_in_grid(n, n, buff=0)
    return g


def recolor(g, values, color=C_PURPLE):
    n = values.shape[0]
    return [g[i * n + j].animate.set_fill(color, opacity=0.08 + 0.85 * min(1, abs(values[i, j])))
            for i in range(n) for j in range(n)]


def arcs_from(src, targets, color=C_YELLOW, widths=None):
    widths = widths or [2] * len(targets)
    return VGroup(*[CurvedArrow(src.get_top() + UP * 0.05, t.get_top() + UP * 0.05, angle=TAU / 5, color=color,
                                stroke_width=w, tip_length=0.15) for t, w in zip(targets, widths)])


class PartTwo(VScene):
    def construct(self):
        # Beat 0: the speed formula from part one
        self.beat(0)
        title = T("Part two", 48).move_to(UP * 0.6)
        sub = T("quantization and context", 30, C_GREY).next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title), FadeIn(sub), run_time=1.0)
        f = speed_formula()
        self.cue("So speed is roughly")
        self.play(FadeOut(title), FadeOut(sub), run_time=0.6)
        self.play(Write(f), run_time=2.0)

        # Beat 1: one lever done, two topics to go
        self.beat(1)
        levers = lever_list()
        self.cue("Part one covered")
        self.play(FadeIn(levers[0], shift=RIGHT * 0.2), run_time=0.8)
        self.cue("This part covers")
        self.play(FadeIn(levers[1], shift=RIGHT * 0.2), run_time=0.8)
        self.cue("And then the other")
        self.play(FadeIn(levers[2], shift=RIGHT * 0.2), run_time=0.8)
        self.play(levers[0].animate.set_opacity(0.4), run_time=0.6)
        self.end()


class Attention(VScene):
    def construct(self):
        # Beat 0: context lives in attention
        self.beat(0)
        toks = sentence()
        self.play(FadeIn(toks, lag_ratio=0.1), run_time=1.5)
        ctx = Brace(toks, DOWN, color=C_GREY)
        ctxl = T("the context: prompt and answer so far", 24, C_GREY).next_to(ctx, DOWN, buff=0.15)
        self.play(GrowFromCenter(ctx), FadeIn(ctxl), run_time=0.8)
        self.cue("we need to look at attention")
        att = T("attention: where tokens look at each other", 28, C_TEAL).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(att), run_time=0.7)

        # Beat 1: query, key, value
        self.beat(1)
        self.play(FadeOut(ctx), FadeOut(ctxl), FadeOut(att), run_time=0.5)
        new = toks[-1]
        self.play(new.animate.set_color(C_YELLOW), run_time=0.4)
        qkv = VGroup(
            VGroup(vec(6, C_YELLOW), T("query: what am I looking for?", 24, C_YELLOW)),
            VGroup(vec(6, C_TEAL), T("key: what do I contain?", 24, C_TEAL)),
            VGroup(vec(6, C_PURPLE), T("value: what do I pass along if picked?", 24, C_PURPLE)),
        )
        for r in qkv:
            r.arrange(RIGHT, buff=0.3)
        qkv.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 1.9)
        for phrase, r in zip(["A query", "A key", "And a value"], qkv):
            self.cue(phrase)
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.6)
        self.cue("compared with the key")
        keys = VGroup(*[vec(4, C_TEAL, cell=0.14).next_to(t, DOWN, buff=0.2) for t in toks[:-1]])
        arcs = arcs_from(new, toks[:-1])
        self.play(FadeIn(keys, lag_ratio=0.1), LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.1),
                  run_time=1.5)
        self.cue("close matches score high")
        scores = VGroup(*[T(f"{s}", 18, C_YELLOW).next_to(k, DOWN, buff=0.12)
                          for s, k in zip([0.4, 2.1, 1.2, 0.4, 3.7, 2.1], keys)])
        self.play(FadeIn(scores, lag_ratio=0.1), run_time=0.8)
        sl = T("score = query · key", 20, C_GREY).next_to(scores, LEFT, buff=0.3)
        self.play(FadeIn(sl), run_time=0.4)

        # Beat 2: weights, blend of values
        self.beat(2)
        self.play(FadeOut(qkv), run_time=0.5)
        weights = VGroup(*[T(f"{w:.2f}", 18, C_YELLOW).move_to(s) for w, s in zip(WEIGHTS, scores)])
        wl = T("weights (sum to 1)", 20, C_GREY).next_to(weights, LEFT, buff=0.3)
        self.play(*[Transform(s, w) for s, w in zip(scores, weights)], Transform(sl, wl), run_time=1.0)
        self.cue("weighted blend")
        values = VGroup(*[vec(4, C_PURPLE, cell=0.14).next_to(s, DOWN, buff=0.15) for s in scores])
        self.play(FadeIn(values), run_time=0.6)
        blend = vec(4, C_PURPLE, cell=0.3).move_to(DOWN * 2.2)
        bl = T("blend of values → what 'it' takes in", 22, C_PURPLE).next_to(blend, DOWN, buff=0.2)
        self.play(*[v.copy().animate.move_to(blend).set_opacity(w) for v, w in zip(values, WEIGHTS)],
                  FadeIn(blend), FadeIn(bl), run_time=1.5)
        self.cue("the word it pulls")
        self.play(arcs[4].animate.set_stroke(width=6), *[a.animate.set_stroke(opacity=0.25) for i, a in
                                                        enumerate(arcs) if i != 4],
                  Indicate(toks[4], color=C_YELLOW), run_time=1.0)

        # Beat 3: heads
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        rows = VGroup()
        code = ["print", "(", "len", "(", "x", ")", ")"]
        for label, words, target, color in (("head 1: the previous word", WORDS, 5, C_YELLOW),
                                            ("head 2: the subject", WORDS, 1, C_TEAL),
                                            ("head 3: the matching bracket", code, 1, C_GOLD)):
            ts = VGroup(*[token_box(w, WHITE, 18) for w in words]).arrange(RIGHT, buff=0.12)
            ts[-1].set_color(color)
            arc = arcs_from(ts[-1], [ts[target]], color, widths=[4])
            lab = T(label, 22, color)
            rows.add(VGroup(lab, VGroup(ts, arc)))
        for r in rows:
            r[0].move_to(LEFT * 4.3)
            r[1].move_to(RIGHT * 1.6)
        for i, r in enumerate(rows):
            r.shift(UP * (2.0 - i * 1.6))
        note = T("each head has its own query, key and value; roles shown are illustrative", 20, C_GREY) \
            .to_edge(DOWN, buff=0.3)
        self.play(FadeIn(rows[0][1][0]), run_time=0.6)
        self.cue("runs several side by side")
        self.play(FadeIn(rows[1][1][0]), FadeIn(rows[2][1][0]), run_time=0.8)
        self.cue("These are the heads")
        self.play(FadeIn(note), run_time=0.5)
        for phrase, r in zip(["the previous word", "the subject", "the matching bracket"], rows):
            self.cue(phrase)
            self.play(FadeIn(r[0]), Create(r[1][1]), run_time=0.7)
        self.cue("Your model has sixteen")
        sixteen = VGroup(*[Square(0.22, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.8) for _ in range(16)]) \
            .arrange(RIGHT, buff=0.06)
        sl = T("16 heads per attention layer", 24, C_YELLOW)
        VGroup(sixteen, sl).arrange(RIGHT, buff=0.3).next_to(note, UP, buff=0.35)
        self.play(FadeIn(sixteen, lag_ratio=0.05), FadeIn(sl), run_time=1.0)

        # Beat 4: grouped-query attention
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        qs = VGroup(*[Square(0.4, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.8) for _ in range(16)]) \
            .arrange(RIGHT, buff=0.1).move_to(UP * 1.6)
        ql = T("16 query heads", 24, C_YELLOW).next_to(qs, UP, buff=0.2)
        self.play(FadeIn(qs, lag_ratio=0.05), FadeIn(ql), run_time=1.0)
        self.cue("share")
        kvs = VGroup()
        for g in range(2):
            pair = VGroup(Rectangle(width=2.6, height=0.45, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8),
                          Rectangle(width=2.6, height=0.45, stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.8)) \
                .arrange(DOWN, buff=0.06)
            pair.add(T("keys", 20).move_to(pair[0]), T("values", 20).move_to(pair[1]))
            kvs.add(pair.move_to([qs[g * 8:(g + 1) * 8].get_x(), -0.9, 0]))
        lines = VGroup(*[Line(q.get_bottom(), kvs[i // 8].get_top(), stroke_width=1.5, color=C_GREY)
                         for i, q in enumerate(qs)])
        kl = T("2 shared key/value heads", 24, C_TEAL).next_to(kvs, DOWN, buff=0.25)
        self.play(FadeIn(kvs), FadeIn(kl), run_time=0.8)
        self.cue("eight queries to each")
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.04), run_time=1.2)
        self.cue("grouped-query")
        name = T("grouped-query attention", 30, C_YELLOW).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(name), run_time=0.6)

        # Beat 5: the KV cache
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        toks = sentence(0.9)
        kv = VGroup(*[VGroup(Rectangle(width=0.5, height=0.26, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8),
                             Rectangle(width=0.5, height=0.26, stroke_width=0, fill_color=C_PURPLE,
                                       fill_opacity=0.8)).arrange(DOWN, buff=0.05).next_to(t, DOWN, buff=0.3)
                      for t in toks[:-1]])
        legend = VGroup(chip("key", C_TEAL, 20), chip("value", C_PURPLE, 20)).arrange(RIGHT, buff=0.3) \
            .to_edge(DOWN, buff=1.6)
        self.play(FadeIn(toks), FadeIn(kv, lag_ratio=0.1), FadeIn(legend), run_time=1.2)
        self.cue("Recomputing them")
        redo = T("recompute every time: the whole prompt again, per token", 24, C_RED).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(redo), run_time=0.6)
        self.cue("So they're computed once")
        box = SurroundingRectangle(kv, buff=0.15, color=C_YELLOW)
        self.play(FadeOut(redo), Create(box), run_time=0.8)
        self.cue("That's the K V cache")
        name = T("KV cache = keys + values", 32, C_YELLOW).to_edge(UP, buff=0.6)
        self.play(FadeIn(name), run_time=0.6)
        self.cue("It grows")
        extra = VGroup(*[token_box(w, WHITE, 22) for w in ["came", "back"]]).arrange(RIGHT, buff=0.18) \
            .next_to(toks, RIGHT, buff=0.18)
        group = VGroup(toks, extra, kv, box)
        self.play(group.animate.shift(LEFT * 1.4), run_time=0.6)
        new_kv = VGroup(*[VGroup(Rectangle(width=0.5, height=0.26, stroke_width=0, fill_color=C_TEAL,
                                           fill_opacity=0.8),
                                 Rectangle(width=0.5, height=0.26, stroke_width=0, fill_color=C_PURPLE,
                                           fill_opacity=0.8)).arrange(DOWN, buff=0.05).next_to(t, DOWN, buff=0.3)
                          for t in [toks[-1], extra[0]]])
        big = SurroundingRectangle(VGroup(kv, new_kv), buff=0.15, color=C_YELLOW)
        self.play(FadeIn(extra), FadeIn(new_kv), Transform(box, big), run_time=1.0)
        self.cue("every new token rereads")
        reread = arcs_from(extra[1], list(toks) + [extra[0]], C_YELLOW)
        self.play(LaggedStart(*[Create(a) for a in reread], lag_ratio=0.08), run_time=1.5)
        self.end()


class DeltaNet(VScene):
    def construct(self):
        rng = np.random.default_rng(3)
        n = 8

        # Beat 0: a list that grows vs a grid that doesn't
        self.beat(0)
        left = T("attention: a list, one entry per token", 24, C_TEAL).move_to(LEFT * 3.4 + UP * 2.6)
        entries = VGroup(*[Rectangle(width=0.3, height=0.3, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8)
                           for _ in range(12)]).arrange(DOWN, buff=0.06).next_to(left, DOWN, buff=0.3)
        right = T("Gated DeltaNet: one fixed grid per head", 24, C_PURPLE).move_to(RIGHT * 3.4 + UP * 2.6)
        state = np.zeros((n, n))
        g = grid(state).next_to(right, DOWN, buff=0.4)
        self.play(FadeIn(left), FadeIn(entries[:3]), run_time=0.6)
        self.cue("a memory that never grows")
        self.play(FadeIn(right), FadeIn(g), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(e) for e in entries[3:]], lag_ratio=0.3), run_time=2.0)
        self.cue("a hundred and twenty-eight")
        size = T("128 × 128 numbers (drawn as 8 × 8)", 22, C_GREY).next_to(g, DOWN, buff=0.25)
        self.play(FadeIn(size), run_time=0.6)
        self.cue("Every token goes into the same grid")
        for k in range(3):
            tok = token_box(WORDS[k + 3], WHITE, 20).move_to(RIGHT * 3.4 + DOWN * 3.2)
            state += np.outer(rng.normal(size=n), rng.normal(size=n)) * 0.3
            self.play(FadeIn(tok), run_time=0.2)
            self.play(tok.animate.move_to(g).scale(0.3).set_opacity(0), *recolor(g, state), run_time=0.7)

        # Beat 1: write = key × value outer product; read = query × grid
        self.beat(1)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not g], FadeOut(size), run_time=0.5)
        self.play(g.animate.move_to(RIGHT * 2.8 + DOWN * 0.2), run_time=0.6)
        k = rng.normal(size=n)
        v = rng.normal(size=n)
        kc = vec(n, C_TEAL, 0.3, k / 2, DOWN).move_to(LEFT * 5.6 + DOWN * 0.2)
        vr = vec(n, C_PURPLE, 0.3, v / 2).move_to(LEFT * 2.6 + UP * 1.4)
        kl = T("key", 22, C_TEAL).next_to(kc, UP, buff=0.15)
        vl = T("value", 22, C_PURPLE).next_to(vr, UP, buff=0.15)
        self.cue("The token's key and value")
        self.play(FadeIn(kc), FadeIn(kl), FadeIn(vr), FadeIn(vl), run_time=0.7)
        outer = np.outer(k, v) / 2
        og = grid(outer, C_GOLD).move_to(LEFT * 2.6 + DOWN * 0.2)
        times = T("×", 32, C_GREY).next_to(kc, RIGHT, buff=0.4)
        self.play(FadeIn(times), FadeIn(og), run_time=0.8)
        self.cue("and added in")
        plus = T("+", 40, C_GREY).move_to((og.get_right() + g.get_left()) / 2)
        state += outer * 0.6
        self.play(FadeIn(plus), og.copy().animate.move_to(g).set_opacity(0), *recolor(g, state), run_time=1.0)
        wl = T("write: memory += key × value", 24, C_GOLD).to_edge(DOWN, buff=0.9)
        self.play(FadeIn(wl), run_time=0.5)
        self.cue("Reading goes")
        self.play(*[FadeOut(m) for m in (kc, kl, vr, vl, times, og, plus)], run_time=0.5)
        q = vec(n, C_YELLOW, 0.3, rng.normal(size=n) / 2, DOWN).next_to(g, LEFT, buff=0.8)
        ql = T("query", 22, C_YELLOW).next_to(q, UP, buff=0.15)
        out = vec(n, C_PURPLE, 0.3, state.T @ np.ones(n) / 4).next_to(g, DOWN, buff=0.5)
        self.play(FadeIn(q), FadeIn(ql), run_time=0.5)
        self.cue("out comes a blend")
        ol = T("blend of values", 22, C_PURPLE).next_to(out, LEFT, buff=0.25)
        self.play(FadeIn(out, shift=DOWN * 0.2), FadeIn(ol), run_time=0.8)
        rl = T("read: query × memory", 24, C_YELLOW).next_to(wl, DOWN, buff=0.15)
        self.play(FadeIn(rl), run_time=0.5)
        self.cue("answered from a summary")
        sm = T("a summary, not a list", 28, C_PURPLE).to_edge(UP, buff=0.6)
        self.play(FadeIn(sm), run_time=0.6)

        # Beat 2: the delta rule
        self.beat(2)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not g], run_time=0.5)
        self.play(g.animate.move_to(RIGHT * 4.2 + DOWN * 0.2), run_time=0.5)
        title = T("a plain sum gets muddy", 28, C_RED).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.5)
        self.cue("they pile on")
        state += np.outer(k, rng.normal(size=n)) * 0.5 + np.outer(k, rng.normal(size=n)) * 0.5
        blur = T("two values under similar keys\nblur into each other", 26, C_RED).move_to(LEFT * 2.5 + DOWN * 0.2)
        self.play(*recolor(g, state), FadeIn(blur), run_time=0.7)
        self.cue("The delta rule")
        self.play(FadeOut(blur), run_time=0.4)
        steps = VGroup(
            VGroup(T("1", 26, C_GREY), T("read what memory holds for this key", 26), vec(5, C_PURPLE, 0.26)),
            VGroup(T("2", 26, C_GREY), T("the new value", 26), vec(5, C_GOLD, 0.26)),
            VGroup(T("3", 26, C_GREY), T("write only the difference", 26, C_YELLOW),
                   vec(5, C_YELLOW, 0.26, [0.1, 0.6, 0.05, 0.3, 0.1])),
        )
        for r in steps:
            r.arrange(RIGHT, buff=0.3)
        steps.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(DOWN * 0.2).to_edge(LEFT, buff=0.6)
        for r in steps:
            r[2].move_to([2.0, r.get_y(), 0])
        self.play(title.animate.become(T("the delta rule", 28, C_GREEN).move_to(title)), run_time=0.4)
        for phrase, r in zip(["reads what the memory", "writes only the difference", "the new value"], steps):
            self.cue(phrase)
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.5)
        self.cue("New information corrects")
        f = T("memory += key × (value − memory's guess for key)", 24, C_YELLOW).to_edge(DOWN, buff=0.6)
        state = state * 0.6
        self.play(FadeIn(f), *recolor(g, state), run_time=0.7)

        # Beat 3: the gate
        self.beat(3)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not g], run_time=0.5)
        self.play(g.animate.move_to(DOWN * 0.2).scale(1.3), run_time=0.6)
        gl = T("gate: multiply the whole grid by a number between 0 and 1", 26, C_GREY).to_edge(UP, buff=0.6)
        self.play(FadeIn(gl), run_time=0.5)
        self.cue("Near one")
        hold = T("× 0.98   holds on", 28, C_GREEN).next_to(g, LEFT, buff=0.6)
        self.play(FadeIn(hold), *recolor(g, state * 0.98), run_time=0.8)
        self.cue("Near zero")
        clear = T("× 0.05   clears out", 28, C_RED).next_to(g, RIGHT, buff=0.6)
        self.play(FadeIn(clear), *recolor(g, state * 0.05), run_time=1.2)
        self.cue("a new document")
        doc = T("e.g. a new document starts", 22, C_GREY).next_to(clear, DOWN, buff=0.2)
        self.play(FadeIn(doc), run_time=0.5)

        # Beat 4: constant work, constant memory
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        pattern = layer_pattern("DDDA" * 10, w=0.24, h=0.5).move_to(UP * 2.2)
        key = VGroup(chip("full attention: 10", C_TEAL, 20), chip("Gated DeltaNet: 30", C_PURPLE, 20)) \
            .arrange(RIGHT, buff=0.4).next_to(pattern, DOWN, buff=0.3)
        self.play(FadeIn(pattern, lag_ratio=0.02), FadeIn(key), run_time=1.2)
        cols, states = VGroup(), VGroup()
        for i, cellm in enumerate(pattern):
            if (i + 1) % 4 == 0:
                cols.add(Rectangle(width=0.2, height=0.05, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8)
                         .move_to([cellm.get_x(), 0.9, 0], aligned_edge=UP))
            else:
                states.add(Square(0.2, stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.8)
                           .move_to([cellm.get_x(), 0.9, 0], aligned_edge=UP))
        self.play(FadeIn(states), FadeIn(cols), run_time=0.6)
        counter = T("tokens: 10", 24, C_GREY).to_edge(DOWN, buff=0.8)
        self.add(counter)
        self.cue("however long")
        tall = [Rectangle(width=0.2, height=2.6, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8)
                .move_to(c.get_top(), aligned_edge=UP) for c in cols]
        self.play(*[Transform(c, t) for c, t in zip(cols, tall)],
                  Transform(counter, T("tokens: 200,000", 24, C_GREY).to_edge(DOWN, buff=0.8)),
                  run_time=4.0, rate_func=linear)
        self.cue("Together they take")
        st = T(f"30 layers × 32 grids: {MATH['moe']['deltanet_state_mb']:.0f} MB, at any length", 26, C_PURPLE) \
            .to_edge(DOWN, buff=1.4)
        self.play(FadeIn(st), run_time=0.6)

        # Beat 5: lossy, so one layer in four keeps exact attention
        self.beat(5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        strip = VGroup(*[Rectangle(width=0.16, height=0.4, stroke_width=0, fill_color=C_DIM, fill_opacity=0.8)
                         for _ in range(60)]).arrange(RIGHT, buff=0.03).move_to(UP * 1.8)
        line = strip[4].copy().set_fill(C_YELLOW, opacity=1)
        sl = T("one exact line, far back", 22, C_YELLOW).next_to(strip[4], UP, buff=0.2).shift(RIGHT * 0.8)
        self.play(FadeIn(strip), run_time=0.6)
        self.cue("can't reliably find")
        self.play(FadeIn(line), FadeIn(sl), run_time=0.6)
        blur = grid(rng.uniform(0.2, 0.6, (n, n))).scale(0.8).move_to(LEFT * 3 + DOWN * 0.8)
        bl = T("summary: blurred", 22, C_PURPLE).next_to(blur, DOWN, buff=0.2)
        self.play(FadeIn(blur), FadeIn(bl), run_time=0.8)
        self.cue("That's why Qwen keeps")
        cache = VGroup(*[Rectangle(width=0.16, height=0.4, stroke_width=0, fill_color=C_TEAL, fill_opacity=0.8)
                         for _ in range(24)]).arrange(RIGHT, buff=0.03).move_to(RIGHT * 3 + DOWN * 0.8)
        cache[2].set_fill(C_YELLOW, opacity=1)
        cl = T("full attention: exact lookup", 22, C_TEAL).next_to(cache, DOWN, buff=0.2)
        self.play(FadeIn(cache), FadeIn(cl), run_time=0.8)
        self.cue("Three layers that summarise")
        pat = layer_pattern("DDDA", w=0.6, h=0.5).to_edge(DOWN, buff=0.9)
        pl = T("3 summarise, then 1 can look anything up", 24).next_to(pat, DOWN, buff=0.2)
        self.play(FadeIn(pat, lag_ratio=0.2), FadeIn(pl), run_time=0.8)
        self.end()
