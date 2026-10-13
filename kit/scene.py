"""Shared style and narration-sync helpers for every video's scenes."""

import inspect
import json
import os
from functools import cache
from pathlib import Path

from manim import *

from kit.voices import EXT, audio_dir, engine, load_narration


@cache
def narration_timing(video_dir, voice):
    """Clip durations for this voice, and for the voice the cues were timed against.

    The voice comes from TTS_VOICE (default: the video's CUE_VOICE). Mid-beat
    cue times (VScene.at) were tuned against CUE_VOICE's reading; other voices
    speak at a different pace, so cues are scaled per beat.
    """
    def durations(v):
        return json.loads((audio_dir(video_dir, v) / "durations.json").read_text())

    cue_voice = load_narration(video_dir).CUE_VOICE
    return durations(voice), durations(cue_voice)


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

BEAT_GAP = 0.45  # default silence after each beat; a video can set its own in narration.py


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
        self._video_dir = Path(inspect.getfile(type(self))).resolve().parent
        self._voice = os.environ.get("TTS_VOICE") or load_narration(self._video_dir).CUE_VOICE
        self._durations, self._cue_reference = narration_timing(self._video_dir, self._voice)
        self._gap = getattr(load_narration(self._video_dir), "BEAT_GAP", BEAT_GAP)

    def _flush(self):
        if self._beat_end is None:
            return
        remaining = self._beat_end - self.renderer.time
        if remaining < -0.05:
            print(f"WARNING {type(self).__name__} beat overran audio by {-remaining:.2f}s")
        if remaining > 0:
            self.wait(remaining)
        self._beat_end = None

    def beat(self, i, gap=None):
        self._flush()
        gap = self._gap if gap is None else gap
        if i > 0 or gap:
            self.wait(gap)
        key = f"{type(self).__name__}_{i}"
        clip = audio_dir(self._video_dir, self._voice) / f"{key}{EXT[engine(self._voice)]}"
        self.add_sound(str(clip))
        self._beat_start = self.renderer.time
        self._beat_end = self._beat_start + self._durations[key]
        self._cue_scale = self._durations[key] / self._cue_reference[key]

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
