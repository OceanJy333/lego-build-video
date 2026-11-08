"""Blender: beat-synced LEGO build in manual order, then a slow hero orbit.

input: -- <seq.glb from order.py> <out dir> [--bpm 125] [--size 1080x1440] [--hold 10] [--frames 0,30,60]
output: <out dir>/f####.png at 30 fps
pos: step 4 of the skill. The manual's groups are split in two halves: the first half lands in 16 even
     batches on the build-up beats (batch 0 is already there at frame 0), the second half in 32 batches on the
     half-beats after the drop (beat 16). One camera per bar, cut on the downbeat; then the hero orbit.
"""
import bpy, sys, math, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('glb'); p.add_argument('out')
p.add_argument('--bpm', type=float, default=125); p.add_argument('--size', default='1080x1440')
p.add_argument('--hold', type=float, default=8, help='seconds of hero orbit after the build')
p.add_argument('--frames', default=None, help='comma list, for previews')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
W, H = map(int, a.size.split('x'))
FPS, BEAT = 30, 60 / a.bpm
DROP_T = 16 * BEAT

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.get('seq') == -1:
        for c in (o, *o.children_recursive): c.hide_render = True
parts = [o for o in sc.objects if o.get('seq', -1) >= 0]
N = 1 + max(o['seq'] for o in parts)

def meshes_of(o): return [c for c in (o, *o.children_recursive) if c.type == 'MESH']
def bbox(objs):
    pts = [m.matrix_world @ Vector(c) for o in objs for m in meshes_of(o) for c in m.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

bpy.context.view_layer.update()
MN, MX = bbox(parts)
C, R = (MN + MX) / 2, (MX - MN).length / 2
for o in parts:
    o['rl'], o['rs'] = o.location.copy(), o.scale.copy()
    lift = Vector((0, 0, R * 0.45))
    o['dl'] = (o.parent.matrix_world.to_3x3().inverted() @ lift) if o.parent else lift
studio.setup(sc, C, R, MN.z, W, H)
sc.render.fps = FPS

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'HORIZONTAL'   # fit the model's width; a portrait frame just shows more floor and sky
def aim(target, az, el, dist, lens=50):
    az, el = math.radians(az), math.radians(el)
    cam.data.lens = lens
    cam.location = target + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

# landing time per group: build-up beats, then half-beats after the drop
S1 = N // 2
def chunk_t(s):
    if s < S1: return -1 if s * 16 // S1 == 0 else (s * 16 // S1) * BEAT
    return DROP_T + ((s - S1) * 32 // (N - S1)) * BEAT / 2
land_t = {s: chunk_t(s) for s in range(N)}
T_END = DROP_T + 31 * BEAT / 2
FALL = min(0.22, BEAT / 2)

# camera target follows the parts landed so far
by_t = {}
for o in parts: by_t.setdefault(land_t[o['seq']], []).append(o)
track, mn, mx = [], Vector((1e9,) * 3), Vector((-1e9,) * 3)
for t in sorted(by_t):
    a0, b0 = bbox(by_t[t]); mn = Vector(map(min, mn, a0)); mx = Vector(map(max, mx, b0))
    track.append((max(0, t), (mn + mx) / 2, max((mx - mn).length / 2, R * 0.12)))
def follow(t):
    if t <= track[0][0]: return track[0][1], track[0][2]
    for (t0, c0, r0), (t1, c1, r1) in zip(track, track[1:]):
        if t < t1:
            u = (t - t0) / (t1 - t0); u = u * u * (3 - 2 * u)
            return c0.lerp(c1, u), r0 + (r1 - r0) * u
    return track[-1][1], track[-1][2]

BARS = [(-128, 32, 2.6, 60), (38, 58, 2.9, 50), (165, 16, 2.3, 55), (-62, 72, 3.2, 45),
        (-28, 12, 2.5, 35), (118, 34, 2.8, 50), (-152, 52, 2.9, 45), (22, 24, 2.6, 50)]
def frame(f):
    t = f / FPS
    for o in parts:
        k = (t - (land_t[o['seq']] - FALL)) / FALL
        if k <= 0: o.scale = (0, 0, 0)
        else:
            k = min(1, k); o.scale = o['rs']; o.location = Vector(o['rl']) + Vector(o['dl']) * (1 - k * k)
    if t < T_END + BEAT:
        c, r = follow(t)
        b = min(int(t / (4 * BEAT)), 7); az, el, k, lens = BARS[b]; u = t / (4 * BEAT) - b
        if b == 4: k *= 1.25 - 0.25 * math.exp(-6 * u)   # drop bar: slammed in close, recoil out
        aim(c, az + 18 * u, el, r * k * (lens / 50), lens)
    else:
        u = t - (T_END + BEAT)
        aim(C + Vector((0, 0, -R * 0.05)), -40 + 6 * u, 20 - 0.4 * u, R * (2.5 - 0.02 * u), 50)

frames = [int(x) for x in a.frames.split(',')] if a.frames else range(0, round((T_END + BEAT + a.hold) * FPS) + 1)
for f in frames:
    frame(f); sc.render.filepath = f'{a.out}/f{f:04d}.png'
    bpy.ops.render.render(write_still=True)
print(f'groups {N} parts {len(parts)} drop {DROP_T:.2f}s done {T_END:.2f}s')
