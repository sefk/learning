#!/bin/sh
# Concatenate rendered 1080p60 scenes into the final video.
#
#   ./build.sh            ElevenLabs "Brian": media/ -> thinking-mode-brian.mp4
#   ./build.sh <voice>    a Kokoro voice, e.g. michael or heart:
#                         media-<voice>/ -> thinking-mode-<voice>.mp4
#
# Each Manim render's audio track ends at its last sound, up to ~2.5s before
# the video does. Joining them with the concat demuxer leaves holes in the
# audio timestamps at every scene boundary, which some players handle by
# dropping audio until the next seek. So pad each scene's audio with silence
# to exactly its video length, then join with the concat filter.
set -e
cd "$(dirname "$0")"
VOICE=${1:-brian}
OUT=thinking-mode-$VOICE.mp4
if [ "$VOICE" = brian ]; then MEDIA=media; else MEDIA=media-$VOICE; fi
if [ ! -d "$MEDIA" ]; then
  echo "no renders in $MEDIA/ (render with TTS_VOICE=$VOICE ... --media_dir $MEDIA)" >&2
  exit 1
fi
SCENES="scenes_a/Intro scenes_a/JustTokens scenes_a/SerialDepth scenes_b/Training scenes_b/Dial scenes_b/Closing"

inputs=""
filters=""
pairs=""
i=0
for s in $SCENES; do
  f="$MEDIA/videos/${s%%/*}/1080p60/${s#*/}.mp4"
  dur=$(ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 "$f")
  inputs="$inputs -i $f"
  filters="$filters[$i:a]aresample=48000,apad=whole_dur=$dur,atrim=duration=$dur[a$i];"
  pairs="$pairs[$i:v][a$i]"
  i=$((i + 1))
done

ffmpeg -v error -y $inputs \
  -filter_complex "${filters}${pairs}concat=n=$i:v=1:a=1[v][a0];[a0]loudnorm=I=-16:TP=-1.5,aresample=48000:async=1:first_pts=0[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart "$OUT"
echo "$OUT"
ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 "$OUT"
