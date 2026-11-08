#!/bin/bash
# input: optional BLENDER (path to an existing Blender binary); macOS with Homebrew ( on Linux install blender, ffmpeg, unzip with the package manager first)
# output: tools under $HOME/.lego-build-video (LDraw parts library, mpd2glb, bun) and env.sh that exports BLENDER, LDRAW_DIR, BUN, MPD2GLB
# pos: step 1 of the lego-build-video skill; safe to run again, it skips what is already there.
set -e
T=$HOME/.lego-build-video; mkdir -p "$T"; cd "$T"
MPD2GLB=0.9.1

if [ -x "$BLENDER" ]; then
  command -v ffmpeg >/dev/null || { echo "Install ffmpeg"; exit 1; }
elif [ "$(uname)" = Darwin ]; then
  command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
  [ -d /Applications/Blender.app ] || brew install --cask blender
  command -v ffmpeg >/dev/null || brew install ffmpeg
  BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
else
  BLENDER=$(command -v blender) || { echo "Install Blender 4.2 or newer (blender.org)"; exit 1; }
  command -v ffmpeg >/dev/null || { echo "Install ffmpeg"; exit 1; }
fi

[ -x bun/bin/bun ] || { curl -fsSL https://bun.sh/install | BUN_INSTALL="$T/bun" bash >/dev/null; }
[ -f mpd2glb.mjs ] || { curl -fsSL -o m.zip "https://github.com/anteloc/mpd2glb/releases/download/v$MPD2GLB/mpd2glb-$MPD2GLB.zip"; unzip -q -o -j m.zip '*/mpd2glb.mjs' -d .; rm m.zip; }
# LDraw parts library, about 100 MB
[ -f ldraw/parts/3001.dat ] || { curl -fsSL -o complete.zip https://library.ldraw.org/library/updates/complete.zip; unzip -q complete.zip; rm complete.zip; }

cat > env.sh <<EOF
export BLENDER="$BLENDER"
export LDRAW_DIR="$T/ldraw"
export BUN="$T/bun/bin/bun"
export MPD2GLB="$T/mpd2glb.mjs"
EOF
. ./env.sh
"$BLENDER" -v | head -1; "$BUN" -v; ffmpeg -version | head -1
echo "ready: source $T/env.sh"
