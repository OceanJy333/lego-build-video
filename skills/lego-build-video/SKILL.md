---
name: lego-build-video
description: Turn an official LEGO set number into a beat-synced video of the set being built, step by step, in the order of the paper manual. Use when someone asks to "build", "assemble" or "render" a LEGO set, or wants to see how a set goes together before buying it.
---

# LEGO build video

Input: a LEGO set, by number (on the box, like `42115` or `10179`) or by name ("the Millennium Falcon", "千年隼"), and optionally a music track.
Output: `build.mp4`, 30 fps. Parts fall into place batch by batch in manual order, synced to the beat; then the finished model turns slowly. Optionally, step 6 makes its mechanisms move.

The model comes from the **LDraw Official Model Repository** (OMR, library.ldraw.org/omr, about 1,470 sets). An LDraw file is plain text: one line per part (colour, position, rotation, part number), with `0 STEP` lines marking the manual's steps. That is why the build order is the real one.

Run every command below from this skill's folder (`SKILL=<path of this folder>; cd "$SKILL"`), or use absolute paths.

## 1. Setup (once)

```bash
scripts/setup.sh            # macOS: installs Blender and ffmpeg with Homebrew if missing; then bun, mpd2glb and the LDraw parts library into ~/.lego-build-video
source ~/.lego-build-video/env.sh
```

About 3 minutes plus the Blender download. Already have Blender? Run `BLENDER=/path/to/Blender scripts/setup.sh` and it is used instead. On Linux install Blender 4.2+, ffmpeg and unzip with the package manager first.

## 2. Get the set

If the user names a set instead of giving its number, search by its official English name (translate it if needed) and confirm the match with the user when there is more than one:

```bash
python3 scripts/fetch_set.py "millennium falcon"   # prints: 10179-1  Millennium Falcon  Star Wars > Ultimate Collector Series  2007, and the mini 4488-1
```

Then download by number:

```bash
python3 scripts/fetch_set.py 10179          # or 10179-1; about a minute
```

By number, it finds the set in the LDraw Official Model Repository and downloads every model file of it (`10179-1.mpd` first = the main build), printing the author, licence and notes. If the set is not there, it says so; tell the user and do not substitute an unofficial file without saying so. Author, licence and any notes about missing parts or substitutes go in the video description.

## 3. Convert and order

```bash
"$BUN" "$MPD2GLB" -l "$LDRAW_DIR" -o set.glb 10179-1.mpd    # 15 s to 2 min for large sets; material warnings are normal
python3 scripts/order.py set.glb set-seq.glb                 # prints: groups N parts M
```

`order.py` walks the model the way the manual does: inside each sub-model, parts go by their own `STEP`; a sub-assembly is complete when it is placed. `groups` is the number of steps with parts; `parts` counts placed parts and is close to, not equal to, the box's piece count. Sub-models named like a display sign (`…-sign.ldr`) are hidden.

## 4. Preview, then render

```bash
"$BLENDER" -b --python scripts/build.py -- set-seq.glb prev --size 1080x1440 --frames 60,240,400,600
```

At 125 BPM these frames are: mid build-up, the drop bar (camera slams in, then backs off), late build, and the hero orbit. Check:

- the floor is light grey, not white;
- the model is not cut off by the frame edge in the orbit frame (600);
- anything above the model is one batch mid-fall (it lands within 0.22 s); a part that stays in the air across frames is a real error.

Then render everything, in the background:

```bash
"$BLENDER" -b --python scripts/build.py -- set-seq.glb frames --size 1080x1440 --bpm 125 --hold 8
```

Cost on an Apple M-series Mac: about 1 minute to load, then 2–6 s per frame depending on part count and size. The default length is about 24 s (720 frames): roughly 30 minutes for a 3,700-part set, an hour for a 5,000-part set.

Timing: the groups are split in half. The first half lands in 16 even batches on the build-up beats (batch 0 is already there at frame 0); the second half lands in 32 batches on the half-beats after the drop (beat 16). The camera cuts every bar. `--bpm` must match the music; with another BPM, scale the preview frames by 125 / BPM.

## 5. Music and encode

Pick a track with a clear build-up and a drop. Find where the 16-beat build-up starts (`START` seconds); the drop must land 16 beats later. Royalty-free sources: Mixkit, Pixabay Music.

```bash
scripts/encode.sh frames music.mp3 START build.mp4
```

## 6. Make it move (optional)

The build video shows how a set goes together. To make its mechanisms move (a radar dish, a crankshaft, doors), hand the same model to [ldraw-mecha](https://github.com/anteloc/ldraw-mecha), an open-source workflow in which the AI reads the LDraw file, finds the parts that can really move, plans the joints and rigs them in Blender.

```bash
git clone https://github.com/anteloc/ldraw-mecha.git ~/ldraw-mecha && cd ~/ldraw-mecha && ./setup-macos.sh   # its own Blender, LeoCAD and tools
```

Then follow its `PROCESS.md` in a new AI session: "Animate data/models-annotated/<set>-1.mpd". About 1,800 sets there are pre-annotated; others need its annotation step first. The AI asks which mechanisms to animate; it only animates joints the model actually has (the 10179 Falcon: radar dish and the two quad-laser turrets; its ramp and landing gear have no hinges, so they stay still). Expect 30–60 minutes for a large set.

Its result is `output/<set>/study/ai-animated.blend`. Re-render it in this skill's studio, camera pushing in on the part that moves most:

```bash
"$BLENDER" -b --python scripts/show_motion.py -- ~/ldraw-mecha/output/<set>/study/ai-animated.blend move 1080 1440
```

`FOCUS_F` (default 210) is the frame used to find the moving part; pick a frame where the main mechanism is away from its rest pose.

## Look

`scripts/studio.py` is a light-grey seamless backdrop, contact shadows from ambient occlusion only, three soft area lights, Standard view transform. Environment overrides: `LEGO_LIGHT` (lights, 0.3), `LEGO_EXPOSURE` (0), `LEGO_BRIGHT` (backdrop, 1.0), `LEGO_FLOOR` (shadow reach, 0.4), `LEGO_VIEW` (`Standard`; `AgX` desaturates bright colours).

## Credits

Keep the LDraw model author, licence (CCAL 2.0) and model notes in the video description. LEGO is a trademark of the LEGO Group, which does not sponsor this.
