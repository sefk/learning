"""Generate narration clips with ElevenLabs, cached by text hash.

Writes audio/<Scene>_<i>.mp3 and audio/durations.json.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from mutagen.mp3 import MP3

from narration import NARRATION

VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian
MODEL_ID = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.55, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}

ROOT = Path(__file__).parent
AUDIO = ROOT / "audio"
CACHE = AUDIO / "cache"


def synth(text, prev_text, next_text, key):
    digest = hashlib.sha256(json.dumps([VOICE_ID, MODEL_ID, SETTINGS, text, prev_text, next_text]).encode()).hexdigest()[:16]
    cached = CACHE / f"{digest}.mp3"
    if cached.exists():
        return cached
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128",
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
    load_dotenv(ROOT.parent / ".env")
    key = os.environ["ELEVEN_LABS_API_KEY"]
    CACHE.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    durations = {}
    for scene, beats in NARRATION.items():
        for i, text in enumerate(beats):
            prev_text = beats[i - 1] if i > 0 else None
            next_text = beats[i + 1] if i + 1 < len(beats) else None
            out = AUDIO / f"{scene}_{i}.mp3"
            if not only or scene in only:
                src = synth(text, prev_text, next_text, key)
                out.write_bytes(src.read_bytes())
            durations[f"{scene}_{i}"] = MP3(out).info.length
        total = sum(v for k, v in durations.items() if k.startswith(scene + "_"))
        print(f"{scene}: {len(beats)} beats, {total:.1f}s")
    (AUDIO / "durations.json").write_text(json.dumps(durations, indent=1))
    print(f"total: {sum(durations.values()) / 60:.1f} min")


if __name__ == "__main__":
    main()
