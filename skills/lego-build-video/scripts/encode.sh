#!/bin/bash
# input: <frames dir with f####.png> <music file> <music start seconds> <out.mp4>
# output: H.264 + AAC video; music starts at START, fades out over the last 1.5 s
# pos: step 5 of the lego-build-video skill
set -e
F=$1; M=$2; S=$3; O=$4
D=$(ls "$F"/f*.png | wc -l | awk '{print $1/30}')
ffmpeg -v error -y -framerate 30 -i "$F/f%04d.png" -ss "$S" -t "$D" -i "$M" \
  -vf "format=yuv420p" -af "afade=t=out:st=$(echo "$D - 1.5" | bc):d=1.5,alimiter=limit=0.95" \
  -c:v libx264 -crf 16 -preset slow -c:a aac -b:a 192k -shortest -movflags +faststart "$O"
echo "$O ${D}s"
