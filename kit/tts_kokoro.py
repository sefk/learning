# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["kokoro>=0.9", "soundfile"]
# ///
"""Generate narration clips locally with Kokoro-82M, cached by text hash.

    uv run kit/tts_kokoro.py <video-dir> <voice>      e.g. thinking-video heart

Writes <video>/audio/<voice>/<Scene>_<i>.wav and durations.json. The clip
cache, <video>/audio/cache-kokoro/, is shared by all voices (the voice is part
of the key) and git-ignored, since it regenerates for free. uv builds an
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kit.voices import VOICES, audio_dir, engine, load_narration  # noqa: E402

SPEED = 1.0
RATE = 24000

# Kokoro's inline pronunciation syntax: [word](/IPA/). Shared by every video;
# a video's narration.py can add its own in a PRONOUNCE dict.
PRONOUNCE = {
    "Qwen": "[Qwen](/kwˈɛn/)",
}


def prepare(text, pronounce):
    for word, hint in pronounce.items():
        text = text.replace(word, hint)
    return text


def synth(cache, pipeline, voice_id, text):
    digest = hashlib.sha256(json.dumps([voice_id, SPEED, text]).encode()).hexdigest()[:16]
    cached = cache / f"{digest}.wav"
    if cached.exists():
        return cached
    # Kokoro splits long input into chunks; join them back into one clip.
    audio = np.concatenate([a for _, _, a in pipeline(text, voice=voice_id, speed=SPEED)])
    sf.write(cached, audio, RATE)
    print(f"  synthesized {digest} ({len(text)} chars)", file=sys.stderr)
    return cached


def main():
    video = Path(sys.argv[1])
    voice = sys.argv[2]
    assert engine(voice) == "kokoro", f"{voice} is a {engine(voice)} voice"
    voice_id = VOICES[voice][1]  # the first letter picks the accent: a = American, b = British
    narration = load_narration(video)
    pronounce = PRONOUNCE | getattr(narration, "PRONOUNCE", {})
    cache = video / "audio" / "cache-kokoro"
    audio = audio_dir(video, voice)
    cache.mkdir(parents=True, exist_ok=True)
    audio.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code=voice_id[0], repo_id="hexgrad/Kokoro-82M")
    durations = {}
    for scene, beats in narration.NARRATION.items():
        for i, text in enumerate(beats):
            out = audio / f"{scene}_{i}.wav"
            out.write_bytes(synth(cache, pipeline, voice_id, prepare(text, pronounce)).read_bytes())
            durations[f"{scene}_{i}"] = sf.info(out).duration
        total = sum(v for k, v in durations.items() if k.startswith(scene + "_"))
        print(f"{scene}: {len(beats)} beats, {total:.1f}s")
    (audio / "durations.json").write_text(json.dumps(durations, indent=1))
    print(f"{voice} total: {sum(durations.values()) / 60:.1f} min -> {audio}")


if __name__ == "__main__":
    main()
