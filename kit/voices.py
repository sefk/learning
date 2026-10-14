"""Narration voices, by the short name used everywhere else (dirs, file names).

No third-party imports: tts_kokoro.py runs in its own environment and reads
this file too.
"""

import importlib.util
from pathlib import Path

VOICES = {
    "brian": ("elevenlabs", "nPczCjzI2devNBz1zQrb"),  # American male, ElevenLabs "Brian"
    "michael": ("kokoro", "am_michael"),  # American male
    "heart": ("kokoro", "af_heart"),  # American female
}

DEFAULT_VOICE = "heart"  # final videos are named without a voice suffix

EXT = {"elevenlabs": ".mp3", "kokoro": ".wav"}


def engine(voice):
    return VOICES[voice][0]


def output_name(stem, voice):
    """<stem>.mp4 for the default voice, <stem>-<voice>.mp4 for any other."""
    return f"{stem}.mp4" if voice == DEFAULT_VOICE else f"{stem}-{voice}.mp4"


def audio_dir(video_dir, voice):
    """Per-scene clips and durations.json for one voice: <video>/audio/<voice>/."""
    return Path(video_dir) / "audio" / voice


def load_narration(video_dir):
    """Import <video>/narration.py by path, so every video can use that name."""
    path = Path(video_dir) / "narration.py"
    spec = importlib.util.spec_from_file_location(f"narration_{Path(video_dir).name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
