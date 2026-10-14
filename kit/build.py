"""Render a video's scenes and join them into the final mp4.

    uv run python -m kit.build <video-dir> [voice] [--render] [--preview]

Scenes come from SCENES in <video>/narration.py; renders go to
<video>/media/<voice>/ and the result to <video>/<SLUG>.mp4. The voice
defaults to Heart; any other voice's output is named <SLUG>-<voice>.mp4. Without --render, existing renders are
joined as they are. --preview renders at 480p15 and only for checking scenes.

A video split into parts lists them in PARTS (part name -> scenes, in play
order), and each part goes to <SLUG>-<part>.mp4. Every scene starts a
chapter, titled from CHAPTERS (scene -> title); the chapter list is written
into the mp4 and printed as timestamps for a video description.

Each Manim render's audio track ends at its last sound, up to ~2.5s before
the video does. Joining them with the concat demuxer leaves holes in the
audio timestamps at every scene boundary, which some players handle by
dropping audio until the next seek. So each scene's audio is padded with
silence to exactly its video length, then joined with the concat filter.
"""

import os
import subprocess
import sys
from pathlib import Path

from kit.voices import DEFAULT_VOICE, load_narration, output_name


def render(video, voice, files, quality):
    env = os.environ | {"TTS_VOICE": voice}
    for file, scenes in files.items():
        subprocess.run(
            ["manim", quality, "--media_dir", str(video / "media" / voice), str(video / f"{file}.py"), *scenes],
            check=True, env=env,
        )


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=duration",
         "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout)


def has_audio(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
         str(path)],
        check=True, capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def chapters_file(path, titles, durations):
    lines, t = [";FFMETADATA1"], 0.0
    for title, d in zip(titles, durations):
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(t * 1000)}", f"END={round((t + d) * 1000)}",
                  f"title={title}"]
        t += d
    path.write_text("\n".join(lines) + "\n")


def timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def join(video, voice, scenes, chapters, out):
    """Join scene renders, given as (file, scene) pairs, into one mp4 with chapters."""
    inputs, filters, pairs, durations = [], [], [], []
    for i, (file, scene) in enumerate(scenes):
        path = video / "media" / voice / "videos" / file / "1080p60" / f"{scene}.mp4"
        if not path.exists():
            sys.exit(f"missing {path} (add --render)")
        if not has_audio(path):
            # seen after re-rendering a scene from Manim's partial-movie cache
            sys.exit(f"{path} has no audio track; re-render it with manim --disable_caching")
        d = duration(path)
        durations.append(d)
        inputs += ["-i", str(path)]
        filters.append(f"[{i}:a]aresample=48000,apad=whole_dur={d},atrim=duration={d}[a{i}];")
        pairs.append(f"[{i}:v][a{i}]")

    titles = [chapters.get(scene, scene) for _, scene in scenes]
    meta = video / "media" / voice / f"{out.stem}-chapters.txt"
    chapters_file(meta, titles, durations)
    n = len(pairs)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", *inputs, "-i", str(meta),
         "-filter_complex",
         "".join(filters) + "".join(pairs)
         + f"concat=n={n}:v=1:a=1[v][a0];[a0]loudnorm=I=-16:TP=-1.5,aresample=48000:async=1:first_pts=0[a]",
         "-map", "[v]", "-map", "[a]", "-map_chapters", str(n),
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)],
        check=True,
    )
    print(f"{out}: {duration(out) / 60:.2f} min")
    t = 0.0
    for title, d in zip(titles, durations):
        print(f"  {timestamp(t)} {title}")
        t += d


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    video = Path(args[0])
    narration = load_narration(video)
    voice = args[1] if len(args) > 1 else DEFAULT_VOICE

    if "--preview" in flags:
        render(video, voice, narration.SCENES, "-ql")
        return
    if "--render" in flags:
        render(video, voice, narration.SCENES, "-qh")

    file_of = {scene: file for file, scenes in narration.SCENES.items() for scene in scenes}
    chapters = getattr(narration, "CHAPTERS", {})
    parts = getattr(narration, "PARTS", None)
    if parts is None:
        join(video, voice, [(f, s) for s, f in file_of.items()], chapters, video / output_name(narration.SLUG, voice))
        return
    for part, scenes in parts.items():
        join(video, voice, [(file_of[s], s) for s in scenes], chapters,
             video / output_name(f"{narration.SLUG}-{part}", voice))


if __name__ == "__main__":
    main()
