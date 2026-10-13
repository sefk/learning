"""Generate narration clips with ElevenLabs, cached by text hash.

    uv run python -m kit.tts_elevenlabs <video-dir> [voice] [Scene ...]

Writes <video>/audio/<voice>/<Scene>_<i>.mp3 and durations.json. Clips are
cached in <video>/audio/cache-elevenlabs/, which is committed: rebuilding from
it makes no API calls. Naming scenes limits synthesis to those scenes.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from mutagen.mp3 import MP3

from kit.voices import VOICES, audio_dir, engine, load_narration

MODEL_ID = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.55, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}

REPO = Path(__file__).resolve().parent.parent


def synth(cache, voice_id, text, prev_text, next_text, key):
    digest = hashlib.sha256(json.dumps([voice_id, MODEL_ID, SETTINGS, text, prev_text, next_text]).encode()).hexdigest()[:16]
    cached = cache / f"{digest}.mp3"
    if cached.exists():
        return cached
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        headers={"xi-api-key": key},
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": SETTINGS,
            "previous_text": prev_text,
            "next_text": next_text,
        },
        timeout=120,
    )
    r.raise_for_status()
    cached.write_bytes(r.content)
    print(f"  synthesized {digest} ({len(text)} chars)", file=sys.stderr)
    return cached


def main():
    video = Path(sys.argv[1])
    voice = sys.argv[2] if len(sys.argv) > 2 else "brian"
    only = set(sys.argv[3:])
    assert engine(voice) == "elevenlabs", f"{voice} is a {engine(voice)} voice"
    voice_id = VOICES[voice][1]
    load_dotenv(REPO / ".env")
    key = os.environ.get("ELEVEN_LABS_API_KEY")
    cache = video / "audio" / "cache-elevenlabs"
    audio = audio_dir(video, voice)
    cache.mkdir(parents=True, exist_ok=True)
    audio.mkdir(parents=True, exist_ok=True)
    durations = {}
    for scene, beats in load_narration(video).NARRATION.items():
        for i, text in enumerate(beats):
            prev_text = beats[i - 1] if i > 0 else None
            next_text = beats[i + 1] if i + 1 < len(beats) else None
            out = audio / f"{scene}_{i}.mp3"
            if not only or scene in only:
                src = synth(cache, voice_id, text, prev_text, next_text, key)
                out.write_bytes(src.read_bytes())
            durations[f"{scene}_{i}"] = MP3(out).info.length
        total = sum(v for k, v in durations.items() if k.startswith(scene + "_"))
        print(f"{scene}: {len(beats)} beats, {total:.1f}s")
    (audio / "durations.json").write_text(json.dumps(durations, indent=1))
    print(f"{voice} total: {sum(durations.values()) / 60:.1f} min -> {audio}")


if __name__ == "__main__":
    main()
