#!/bin/bash
# Perbesar klip sumber ke 1080x1920 (lanczos + sedikit tajam) -> public/prep/cNN.mp4
# Berlaku untuk klip 360p maupun 720p/1080p. Fps asli dipertahankan.
set -e
cd "$(dirname "$0")/.."
mkdir -p public/prep
for f in public/clips/c*.mp4; do
  n=$(basename "$f")
  ffmpeg -y -v error -i "$f" -an \
    -vf "hqdn3d=1.2:1.2:4:4,scale=1080:1920:flags=lanczos,unsharp=5:5:0.7:3:3:0.0" \
    -c:v libx264 -preset medium -crf 15 -pix_fmt yuv420p -g 24 -movflags +faststart "public/prep/$n"
done
echo "prep selesai"
