# How thinking mode works — explainer video

A ~7.7 minute explainer, in the style of [3Blue1Brown][3b1b], on how "thinking"
(reasoning) mode works in modern LLMs. Written for someone who already knows
training, backprop, and inference, and who uses LLMs heavily — including the
local Qwen builds benchmarked in [`../../bench`][bench].

There are three versions with identical visuals, named after the narrator's
voice. All are 1080p60, built with the shared tools in [`../kit`][kit]:

| File | Voice | Engine | Length |
|------|-------|--------|--------|
| `thinking-mode-brian.mp4` | Brian, American male | [ElevenLabs][el] (cloud, `eleven_multilingual_v2`) | 7:42 |
| `thinking-mode-michael.mp4` | Michael (`am_michael`), American male | [Kokoro-82M][kokoro] (local) | 8:29 |
| `thinking-mode-heart.mp4` | Heart (`af_heart`), American female | [Kokoro-82M][kokoro] (local) | 7:46 |

The videos aren't committed: H.264 doesn't delta-compress, so every re-render
would add a full copy to git history forever. Instead, publish each version
as a GitHub Release asset, which sits outside the repo and doesn't count
toward its size:

```sh
gh release create thinking-video-v1 thinking-video/thinking-mode-*.mp4
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

The pipeline (TTS, narration-synced scenes, assembly) is shared by every video
in this repo and documented in the [top-level README][top]. Specific to this
one:

- **Narration** — `narration.py` holds the script, split into *beats* (one
  audio clip each), plus the scene list and `CUE_VOICE = "brian"`: the
  mid-beat cues in the scenes were timed against Brian's reading, and are
  scaled per beat for the other voices.
- **Animation** — [Manim Community][manim] scenes in `scenes_a.py` (Intro,
  JustTokens, SerialDepth) and `scenes_b.py` (Training, Dial, Closing).
- **Audio** — `audio/cache-elevenlabs/` holds every ElevenLabs clip and is
  committed, which saves the credits: rebuilding Brian's clips from it makes
  no API calls. The per-voice clips in `audio/<voice>/` and the Kokoro cache
  are git-ignored, since they regenerate for free.

## Rebuilding

From the repo root:

```sh
uv run python -m kit.tts_elevenlabs thinking-video brian   # Brian's clips, from the cache
uv run kit/tts_kokoro.py thinking-video heart              # or a Kokoro voice
uv run python -m kit.build thinking-video heart --render   # → thinking-video/thinking-mode-heart.mp4
```

The ElevenLabs step reads `ELEVEN_LABS_API_KEY` from `../.env`, but only
calls the API for beats that aren't cached. A full 1080p60 render of all six
scenes takes a few minutes on an M1 Max.

## About the voices

- Michael reads ~10% slower than Brian (8:29 vs 7:42), Heart about the same
  (7:46). The animation follows each voice's own clip lengths.
- `am_michael` is the closest stock Kokoro match to ElevenLabs' "Brian";
  `af_heart` is the highest-rated voice in Kokoro's own quality ratings, well
  above its male voices.
- Without a pronunciation hint, Kokoro reads "Qwen" as the spelled-out letters
  "Q-wen"; the fix lives in `kit/tts_kokoro.py`.

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
[kit]: ../kit/
[top]: ../README.md
[bench]: ../../bench/README.md
[merrill]: https://arxiv.org/abs/2310.07923
[r1]: https://arxiv.org/abs/2501.12948
[s1]: https://arxiv.org/abs/2501.19393
[faithful]: https://arxiv.org/abs/2505.05410
[el]: https://elevenlabs.io/
[manim]: https://www.manim.community/
[kokoro]: https://huggingface.co/hexgrad/Kokoro-82M
