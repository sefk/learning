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
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kit.voices import VOICES, audio_dir, engine, load_narration  # noqa: E402

SPEED = 1.0  # a video can set KOKORO_SPEED in narration.py (below 1 is slower)
RATE = 24000

# Words Kokoro gets wrong, with the phonemes to say instead. Shared by every
# video; a video's narration.py can add its own in a PRONOUNCE dict. Phonemes
# use Kokoro's (misaki's) alphabet: IPA plus A = "ay", I = "eye", O = "oh";
# ˈ marks primary stress, ˌ secondary. To see what Kokoro would say on its
# own: misaki.en.G2P()(text). Matching is whole-word and ignores case, and
# each inflection needs its own entry.
PRONOUNCE = {
    "Qwen": "kwˈɛn",
    "prefill": "pɹˈifˌɪl",  # not pre-FILL
    "prefills": "pɹˈifˌɪlz",
    "prefilled": "pɹˈifˌɪld",
    "prefilling": "pɹˈifˌɪlɪŋ",
    "overhead": "ˈOvəɹhˌɛd",  # the noun, not over-HEAD
    "A three B": "ˈA θɹˈi bˈi",  # the letter, not the article ("uh three B")
    "SWE-bench": "swˈibˌɛnʧ",  # "swee", not spelled out
    "GPT-OSS": "ʤˌipˌitˈi ˈOˌɛsˈɛs",  # stress the O, or it blurs into "USS"
    "kilobyte": "kˈɪləbˌIt",  # KIL-o, not KEE-lo
    "kilobytes": "kˈɪləbˌIts",
}


def prepare(text, pronounce):
    # Kokoro's inline syntax is [word](/phonemes/); the matched text is kept.
    for word, phonemes in pronounce.items():
        text = re.sub(rf"\b{re.escape(word)}\b", lambda m: f"[{m[0]}](/{phonemes}/)", text, flags=re.I)
    return text


def synth(cache, pipeline, voice_id, speed, text):
    digest = hashlib.sha256(json.dumps([voice_id, speed, text]).encode()).hexdigest()[:16]
    cached = cache / f"{digest}.wav"
    if cached.exists():
        return cached
    # Kokoro splits long input into chunks; join them back into one clip.
    audio = np.concatenate([a for _, _, a in pipeline(text, voice=voice_id, speed=speed)])
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
    speed = getattr(narration, "KOKORO_SPEED", SPEED)
    cache = video / "audio" / "cache-kokoro"
    audio = audio_dir(video, voice)
    cache.mkdir(parents=True, exist_ok=True)
    audio.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code=voice_id[0], repo_id="hexgrad/Kokoro-82M")
    durations = {}
    for scene, beats in narration.NARRATION.items():
        for i, text in enumerate(beats):
            out = audio / f"{scene}_{i}.wav"
            out.write_bytes(synth(cache, pipeline, voice_id, speed, prepare(text, pronounce)).read_bytes())
            durations[f"{scene}_{i}"] = sf.info(out).duration
        total = sum(v for k, v in durations.items() if k.startswith(scene + "_"))
        print(f"{scene}: {len(beats)} beats, {total:.1f}s")
    (audio / "durations.json").write_text(json.dumps(durations, indent=1))
    print(f"{voice} total: {sum(durations.values()) / 60:.1f} min -> {audio}")


if __name__ == "__main__":
    main()
