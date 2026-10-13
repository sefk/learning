# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["kokoro>=0.9", "soundfile"]
# ///
"""Generate narration clips locally with Kokoro-82M, cached by text hash.

Same layout as tts.py, but per voice: `uv run tts_kokoro.py af_heart` writes
audio-kokoro/heart/<Scene>_<i>.wav and audio-kokoro/heart/durations.json
(default voice am_michael). The first letter of a Kokoro voice id picks the
accent: a = American, b = British. uv builds an
isolated Python 3.12 environment from the header above (Kokoro doesn't
support the project's Python yet).
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from narration import NARRATION

DEFAULT_VOICE = "am_michael"
SPEED = 1.0
RATE = 24000

# Kokoro's inline pronunciation syntax: [word](/IPA/)
PRONOUNCE = {
    "Qwen": "[Qwen](/kwˈɛn/)",
}

ROOT = Path(__file__).parent
CACHE = ROOT / "audio-kokoro" / "cache"  # shared by all voices; the voice is in the key


def prepare(text):
    for word, hint in PRONOUNCE.items():
        text = text.replace(word, hint)
    return text


def synth(pipeline, voice, text):
    digest = hashlib.sha256(json.dumps([voice, SPEED, prepare(text)]).encode()).hexdigest()[:16]
    cached = CACHE / f"{digest}.wav"
    if cached.exists():
        return cached
    # Kokoro splits long input into chunks; join them back into one clip.
    audio = np.concatenate([a for _, _, a in pipeline(prepare(text), voice=voice, speed=SPEED)])
    sf.write(cached, audio, RATE)
    print(f"  synthesized {digest} ({len(text)} chars)", file=sys.stderr)
    return cached


def main():
    voice = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VOICE
    audio = ROOT / "audio-kokoro" / voice.split("_", 1)[1]  # am_michael -> michael
    audio.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")
    durations = {}
    for scene, beats in NARRATION.items():
        for i, text in enumerate(beats):
            out = audio / f"{scene}_{i}.wav"
            out.write_bytes(synth(pipeline, voice, text).read_bytes())
            durations[f"{scene}_{i}"] = sf.info(out).duration
        total = sum(v for k, v in durations.items() if k.startswith(scene + "_"))
        print(f"{scene}: {len(beats)} beats, {total:.1f}s")
    (audio / "durations.json").write_text(json.dumps(durations, indent=1))
    print(f"{voice} total: {sum(durations.values()) / 60:.1f} min -> {audio}")


if __name__ == "__main__":
    main()
