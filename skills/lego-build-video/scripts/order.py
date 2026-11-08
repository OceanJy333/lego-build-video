#!/usr/bin/env python3
"""Tag every LEGO part in an mpd2glb file with its global build-step index.

input: mpd2glb .glb (nodes carry LDraw buildingStep), output .glb path
output: same .glb, part nodes named P<idx> with extras.seq = build-step group
pos: step 3 of the lego-build-video skill; build.py reads extras.seq in Blender.
Order: walk the model tree; inside each (sub)model, parts go by their own step;
a submodel is fully built at the moment it is placed, like the paper manual.
"""
import json, re, struct, sys

src, dst = sys.argv[1:3]
raw = open(src, 'rb').read()
jlen = struct.unpack('<I', raw[12:16])[0]
gl = json.loads(raw[20:20 + jlen])
rest = raw[20 + jlen:]
nodes = gl['nodes']
def is_part(n):
    # official or unofficial part, or a generated flex hose/spring/string drawn as plain meshes
    t = n.get('extras', {}).get('type') or ''
    return 'Part' in t or any('mesh' in nodes[k] for k in n.get('children', []))

seq = 0
def build(i, skip=False):
    """Emit this submodel's steps; returns nothing, numbers parts via global seq."""
    global seq
    kids = nodes[i].get('children', [])
    skip = skip or bool(re.search(r'(^|[^a-z])sign([^a-z]|$)', (nodes[i].get('extras', {}).get('fileName') or '').lower()))  # display sign, not part of the model
    by_step = {}
    for k in kids:
        by_step.setdefault(nodes[k].get('extras', {}).get('buildingStep', 0), []).append(k)
    for step in sorted(by_step):
        group = []
        for k in by_step[step]:
            if is_part(nodes[k]):
                group.append(k)
            elif nodes[k].get('children'):
                build(k, skip)    # sub-assembly finished before it is placed
        for k in group:
            nodes[k]['name'] = f'P{k:05d}'
            nodes[k].setdefault('extras', {})['seq'] = -1 if skip else seq
        if group and not skip:
            seq += 1

root = gl['scenes'][gl.get('scene', 0)]['nodes'][0]
build(root)
print('groups', seq, 'parts', sum(1 for n in nodes if 'seq' in n.get('extras', {})))
js = json.dumps(gl, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
out = raw[:12] + struct.pack('<I', len(js)) + b'JSON' + js + rest
out = out[:8] + struct.pack('<I', len(out)) + out[12:]
open(dst, 'wb').write(out)
