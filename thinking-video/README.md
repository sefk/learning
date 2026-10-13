# How thinking mode works — explainer video

A ~7.7 minute explainer, in the style of [3Blue1Brown][3b1b], on how "thinking"
(reasoning) mode works in modern LLMs. Written for someone who already knows
training, backprop, and inference, and who uses LLMs heavily — including the
local Qwen builds benchmarked in [`../../bench`][bench].

Output: **`thinking-mode.mp4`** (1080p60, 7:42, ~23 MB), built by `build.sh`.
The video isn't committed: H.264 doesn't delta-compress, so every re-render
would add a full copy to git history forever. Instead, publish each version
as a GitHub Release asset, which sits outside the repo and doesn't count
toward its size:

```sh
gh release create thinking-video-v1 thinking-video/thinking-mode.mp4
```

## What it covers

| # | Scene | Idea |
|---|-------|------|
| 0 | `Intro` | Thinking on vs. off is the same weights; the model just writes more first. |
| 1 | `JustTokens` | The chat template; `<think>` is ordinary generated text; the server splits it into `reasoning_content` vs. `content`; why an empty `<think></think>` prefill turns thinking off (Qwen3's `enable_thinking=False` template does exactly that). |
| 2 | `SerialDepth` | Each token gets a fixed-height stack of layers. A sampled token is fed back in as the next position's input, so serial depth goes from L to L × N. Tokens as scratchpad; head vs. paper; chain-of-thought expressivity ([Merrill & Sabharwal][merrill]). |
| 3 | `Training` | "Let's think step by step" → RL on verifiable rewards: sample a group of attempts, grade only final answers, advantage = reward − group mean. Response length and "Wait," emerge ([DeepSeek-R1][r1]). Distillation into small local models. |
| 4 | `Dial` | Accuracy vs. log thinking tokens; test-time compute; effort/budgets and forced `</think>`; budget forcing with "Wait" ([s1][s1]); cost, using the bench finding that 300+ thinking tokens per MCQ item turns a run into ~10 hours. |
| 5 | `Closing` | Traces are load-bearing but not guaranteed faithful ([Chen et al.][faithful]); summarized vs. raw traces; recap. |

The accuracy-vs-tokens and length-vs-RL-steps charts are illustrative shapes,
not real data, and are labelled as such on screen.

## How it's built

- **Narration** — `narration.py` holds the script, split into *beats* (one
  audio clip each).
- **TTS** — `tts.py` sends each beat to [ElevenLabs][el] (voice "Brian",
  `eleven_multilingual_v2`, with neighbouring beats passed as
  `previous_text`/`next_text` for continuous prosody). Clips are cached in
  `audio/cache/` by a hash of text + voice + settings, so only edited beats are
  re-synthesized. Writes `audio/<Scene>_<i>.mp3` and `audio/durations.json`.
  The cache is committed, which saves the ElevenLabs credits; the per-scene
  copies and `durations.json` are git-ignored, since `tts.py` rebuilds them
  from the cache without calling the API.
- **Animation** — [Manim Community][manim] scenes in `scenes_a.py` (Intro,
  JustTokens, SerialDepth) and `scenes_b.py` (Training, Dial, Closing).
  `common.py` provides `VScene`, which syncs animation to narration:
  `self.beat(i)` starts clip *i*, `self.at(t)` waits until *t* seconds into the
  clip, and the next `beat()` pads out whatever audio remains. So the timing adjusts
  automatically when narration changes. A beat that overruns its audio prints
  `WARNING <Scene> beat overran audio`.
- **Assembly** — `build.sh` concatenates the six 1080p60 renders, re-encodes
  to H.264, and loudness-normalizes the audio (−16 LUFS). Manim's audio track
  stops at the scene's last sound, up to ~2.5 s before its video does, so each
  scene's audio is padded with silence to its video length before joining.
  Without that padding the audio track has holes at scene boundaries, and some
  players drop sound there until you seek.

Fonts are Charter (prose) and Menlo (code), both stock macOS; no LaTeX needed.

## Rebuilding

Needs `uv` and `ffmpeg`. The API key is read from `ELEVEN_LABS_API_KEY` in
`../.env` (only text-to-speech permission is needed).

```sh
uv run python tts.py                          # (re)synthesize changed beats
uv run manim -ql scenes_a.py SerialDepth      # quick 480p15 preview of one scene
uv run manim -qh scenes_a.py Intro JustTokens SerialDepth
uv run manim -qh scenes_b.py Training Dial Closing
./build.sh                                    # → thinking-mode.mp4
```

A full 1080p60 render of all six scenes takes a few minutes on an M1 Max.

## Local narration with Kokoro

A comparison version uses [Kokoro-82M][kokoro], an open-weights (Apache 2.0)
TTS model that runs locally. It's free and needs no API key.

```sh
uv run tts_kokoro.py                          # → audio-kokoro/
TTS_BACKEND=kokoro uv run manim -qh --media_dir media-kokoro scenes_a.py Intro JustTokens SerialDepth
TTS_BACKEND=kokoro uv run manim -qh --media_dir media-kokoro scenes_b.py Training Dial Closing
./build.sh kokoro                             # → thinking-mode-kokoro.mp4
```

- `tts_kokoro.py` declares its own dependencies inline (PEP 723), so `uv run`
  builds a separate Python 3.12 environment for it, since Kokoro doesn't
  support the project's Python yet. The first run downloads the model
  (~330 MB) and a spaCy English model. After that it narrates ~5× faster than
  real time on an M1 Max, so the whole script takes a couple of minutes.
- Voice is `am_michael`, the closest stock match to ElevenLabs' "Brian".
  Other male voices worth trying: `am_fenrir`, `am_puck`, `bm_george`
  (British).
- Pronunciation fixes go in `PRONOUNCE`, using Kokoro's `[word](/IPA/)`
  syntax. Without that, "Qwen" comes out as the spelled-out letters "Q-wen".
- Kokoro reads ~10% slower (8:29 vs 7:42 overall). `common.py` scales
  the mid-beat animation cues by each beat's duration ratio against the
  ElevenLabs clips, so the visuals stay on the right words. That means
  `audio/durations.json` must exist; `uv run python tts.py` rebuilds it from
  the committed cache without calling the API.
- Everything Kokoro-related is git-ignored, since it all regenerates locally.

## What it cost

On the ElevenLabs **free plan**, as I understand it, you get 10,000 credits a
month, and `eleven_multilingual_v2` costs 1 credit per character.

| Item | Usage | Cost |
|------|-------|------|
| ElevenLabs TTS | 7,098 characters of narration in 32 clips, each synthesized once, plus a ~55-character test clip: **≈ 7,150 credits** | **$0**, but about **72% of the monthly free quota**. That leaves roughly 2,850 characters this month for re-recording edited beats. |
| Claude Code session | Writing the script and scenes, rendering, reviewing frames | Not measured here. Run `/cost` in the session for the actual number. |
| Rendering | Local Manim + ffmpeg | $0 |

Implications of the free tier:

- **Budget edits.** A typical beat is 150–370 characters, so ~2,850 remaining
  credits covers about 10–15 re-recorded beats this month. Re-synthesizing the
  whole video needs a fresh month's quota. `tts.py` only calls the API for beats
  whose text changed, so small edits are cheap. Note that editing a beat also
  invalidates its neighbours, because they pass it as `previous_text`/`next_text`.
- **Licensing.** The free plan is for non-commercial use and requires crediting
  ElevenLabs. That's fine for a personal explainer, but publishing it
  commercially would need a paid plan.

The exact figure isn't recorded because the API key lacks the `user_read`
permission needed to query usage. The ElevenLabs usage page shows the real
remaining balance.

[3b1b]: https://www.3blue1brown.com/
[bench]: ../../bench/README.md
[merrill]: https://arxiv.org/abs/2310.07923
[r1]: https://arxiv.org/abs/2501.12948
[s1]: https://arxiv.org/abs/2501.19393
[faithful]: https://arxiv.org/abs/2505.05410
[el]: https://elevenlabs.io/
[manim]: https://www.manim.community/
[kokoro]: https://huggingface.co/hexgrad/Kokoro-82M
