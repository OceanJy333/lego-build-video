"""Blender: re-render an ldraw-mecha ai-animated.blend in the shared paper studio, camera pushing in on the part that moves most.

input: -- <ai-animated.blend> <out dir> [W H] [frame list]
output: <out dir>/f####.png at the blend's own fps and frame range
pos: step 6 of the lego-build-video skill: the "it moves" shot after the build (tested on 10179: radar dish turns, turrets swing).
The focus part is found by motion: parts whose world position differs between the first frame and FOCUS_F.
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
src, OUT = a[0], a[1]
W, H = (int(a[2]), int(a[3])) if len(a) > 3 else (1080, 1440)
ONLY = [int(x) for x in a[4].split(',')] if len(a) > 4 else None
FOCUS_F = int(os.environ.get('FOCUS_F', '210'))   # Falcon: only the dish is off its rest pose here

bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
for o in [o for o in sc.objects if o.type in ('LIGHT', 'CAMERA')]: bpy.data.objects.remove(o)
meshes = [o for o in sc.objects if o.type == 'MESH' and o.visible_get()]
def centres(f):
    sc.frame_set(f); bpy.context.view_layer.update()
    return {o.name: o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8) for o in meshes}
c0, c1 = centres(sc.frame_start), centres(FOCUS_F)
moving = [o for o in meshes if (c0[o.name] - c1[o.name]).length > 1e-3]
sc.frame_set(sc.frame_start)
def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
mn, mx = bbox(meshes); C, R = (mn + mx) / 2, (mx - mn).length / 2
fm, fx = bbox(moving); F = (fm + fx) / 2
studio.setup(sc, C, R, mn.z, W, H)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'HORIZONTAL'; cam.data.lens = 50
n0, n1 = sc.frame_start, sc.frame_end
def shoot(f):
    u = (f - n0) / (n1 - n0); e = u * u * (3 - 2 * u)
    target = C.lerp(F, 0.75 * e)
    az, el, d = math.radians(-35 + 25 * u), math.radians(48 + 10 * e), R * (1.9 - 0.8 * e)
    cam.location = target + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * d
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
print('moving parts', len(moving), 'focus', tuple(round(v, 3) for v in F), 'fps', sc.render.fps, 'frames', n0, n1)
for f in (ONLY or range(n0, n1 + 1)):
    sc.frame_set(f); shoot(f); sc.render.filepath = f'{OUT}/f{f:04d}.png'
    bpy.ops.render.render(write_still=True)
