"""Shared style and narration-sync helpers for all scenes."""

import json
import os
from pathlib import Path

from manim import *

ROOT = Path(__file__).parent

# Which narration to sync to, by voice: TTS_VOICE=brian (default; ElevenLabs,
# audio/*.mp3) or a Kokoro voice such as michael or heart
# (audio-kokoro/<voice>/*.wav, made by tts_kokoro.py).
VOICE = os.environ.get("TTS_VOICE", "brian")
if VOICE == "brian":
    AUDIO_DIR, AUDIO_EXT = ROOT / "audio", ".mp3"
else:
    AUDIO_DIR, AUDIO_EXT = ROOT / "audio-kokoro" / VOICE, ".wav"
DURATIONS = json.loads((AUDIO_DIR / "durations.json").read_text())
# Mid-beat cue times (VScene.at) were tuned against the ElevenLabs reading;
# other voices speak at a different pace, so cues are scaled per beat.
CUE_REFERENCE = json.loads((ROOT / "audio" / "durations.json").read_text())

BG = "#0e0f13"
SERIF = "Charter"
MONO = "Menlo"

# 3b1b-ish palette
C_BLUE = "#58C4DD"
C_TEAL = "#5CD0B3"
C_YELLOW = "#FFFF00"
C_GOLD = "#F0AC5F"
C_RED = "#FC6255"
C_GREEN = "#83C167"
C_GREY = "#888888"
C_DIM = "#4a4d55"
C_PURPLE = "#9A72AC"

config.background_color = BG

BEAT_GAP = 0.45  # silence after each beat


def T(text, size=36, color=WHITE, **kw):
    return Text(text, font=SERIF, font_size=size, color=color, **kw)


def M(text, size=28, color=WHITE, **kw):
    return Text(text, font=MONO, font_size=size, color=color, **kw)


class VScene(Scene):
    """Scene whose pacing follows narration clips.

    Usage: self.beat(i) starts clip i; animations follow; the next beat()
    (or self.end()) waits out whatever audio remains.
    """

    def setup(self):
        self._beat_end = None

    def _flush(self):
        if self._beat_end is None:
            return
        remaining = self._beat_end - self.renderer.time
        if remaining < -0.05:
            print(f"WARNING {type(self).__name__} beat overran audio by {-remaining:.2f}s")
        if remaining > 0:
            self.wait(remaining)
        self._beat_end = None

    def beat(self, i, gap=BEAT_GAP):
        self._flush()
        if i > 0 or gap:
            self.wait(gap)
        key = f"{type(self).__name__}_{i}"
        self.add_sound(str(AUDIO_DIR / f"{key}{AUDIO_EXT}"))
        self._beat_start = self.renderer.time
        self._beat_end = self._beat_start + DURATIONS[key]
        self._cue_scale = DURATIONS[key] / CUE_REFERENCE[key]

    def at(self, t):
        """Wait until t seconds into the current beat's clip (no-op if already past)."""
        remaining = self._beat_start + t * self._cue_scale - self.renderer.time
        if remaining > 0:
            self.wait(remaining)

    def left(self):
        """Seconds of audio remaining in the current beat."""
        return max(0.0, self._beat_end - self.renderer.time)

    def end(self, tail=1.0):
        self._flush()
        self.wait(tail)


def layer_stack(n=6, w=0.55, h=0.32, gap=0.08, color=C_BLUE):
    """A column of rounded rectangles: one token position's layers."""
    rects = VGroup(*[
        RoundedRectangle(width=w, height=h, corner_radius=0.06, stroke_color=color,
                         stroke_width=2, fill_color=color, fill_opacity=0.15)
        for _ in range(n)
    ]).arrange(UP, buff=gap)
    return rects


def token_box(text, color=WHITE, size=22, pad=0.12):
    label = M(text, size=size, color=color)
    box = SurroundingRectangle(label, buff=pad, corner_radius=0.06, stroke_color=color,
                               stroke_width=1.5)
    return VGroup(box, label)
