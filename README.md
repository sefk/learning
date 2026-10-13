# Learning

Explainer videos in the style of [3Blue1Brown][3b1b], made with Claude Code,
[Manim][manim] and text-to-speech. Each video lives in its own directory with
its script, scenes and a README; the tooling they share lives in `kit/`.

| Video | About |
|-------|-------|
| [`thinking-video`][thinking] | How "thinking" (reasoning) mode works in modern LLMs |

The rendered videos aren't committed (H.264 doesn't delta-compress, so every
re-render would add a full copy to git history). They're published as GitHub
Release assets instead, e.g.:

```sh
gh release create thinking-video-v1 thinking-video/thinking-mode-*.mp4
```

## How a video is made

Each video directory has a `narration.py` with:

- `NARRATION`: the script, split into *beats* per scene (one audio clip each).
- `SCENES`: scene file → scene classes, in play order.
- `SLUG`: the output name, `<SLUG>-<voice>.mp4`.
- `CUE_VOICE`: the voice the scenes' mid-beat cues were timed against.
- Optionally, `BEAT_GAP` (seconds of silence between beats, default 0.45),
  `KOKORO_SPEED` (default 1.0; lower is slower) and `PRONOUNCE` (extra
  Kokoro pronunciation hints), for pacing a video differently.

The steps, run from the repo root:

```sh
uv run python -m kit.tts_elevenlabs <video> brian      # or:
uv run kit/tts_kokoro.py <video> heart                 # → <video>/audio/<voice>/
uv run python -m kit.build <video> heart --preview     # 480p15 renders to check scenes
uv run python -m kit.build <video> heart --render      # 1080p60 → <video>/<SLUG>-heart.mp4
```

Without `--render`, `kit.build` just reassembles the existing renders.

## The kit

- **`voices.py`** — the voices, by the short name used everywhere else:
  `brian` ([ElevenLabs][el], cloud), `michael` and `heart` ([Kokoro-82M][kokoro],
  local). Add a voice here to use it.
- **`tts_elevenlabs.py`** — synthesizes each beat via the ElevenLabs API,
  passing the neighbouring beats as `previous_text`/`next_text` for continuous
  prosody. Clips are cached in `<video>/audio/cache-elevenlabs/` by a hash of
  text, neighbours, voice and settings; that cache is committed, so only
  edited beats (and their neighbours) cost credits. Reads
  `ELEVEN_LABS_API_KEY` from `.env` (see `.env.example`).
- **`tts_kokoro.py`** — the same for [Kokoro-82M][kokoro], an open-weights
  (Apache 2.0) TTS model that runs locally, free, at ~5× real time on an M1
  Max. It declares its own dependencies (PEP 723), so `uv run` builds a
  separate Python 3.12 environment for it; the first run downloads the model
  (~330 MB). Pronunciation fixes go in `PRONOUNCE`, using Kokoro's
  `[word](/IPA/)` syntax, or in a video's own `PRONOUNCE` dict.
- **`scene.py`** — style (palette, Charter and Menlo fonts, no LaTeX needed),
  helpers, and `VScene`, which syncs animation to narration: `self.beat(i)`
  starts clip *i*, `self.at(t)` waits until *t* seconds into the clip, and the
  next `beat()` pads out whatever audio remains, so timing follows the
  narration automatically. Cue times are scaled per beat for voices other
  than `CUE_VOICE`. A beat that overruns its audio prints
  `WARNING <Scene> beat overran audio`. The voice comes from `TTS_VOICE`
  (default: `CUE_VOICE`).
- **`build.py`** — renders the scenes and joins them into one H.264 file with
  loudness-normalized audio (−16 LUFS). Manim's audio track stops at a scene's
  last sound, up to ~2.5 s before its video does, so each scene's audio is
  padded with silence to its video length before joining. Without that padding
  the audio track has holes at scene boundaries, and some players drop sound
  there until you seek.

Needs `uv` and `ffmpeg`.

[3b1b]: https://www.3blue1brown.com/
[manim]: https://www.manim.community/
[el]: https://elevenlabs.io/
[kokoro]: https://huggingface.co/hexgrad/Kokoro-82M
[thinking]: thinking-video/README.md
