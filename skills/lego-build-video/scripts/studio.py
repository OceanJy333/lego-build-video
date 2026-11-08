"""Paper studio for the LEGO build renders: light-grey seamless backdrop, floor that only carries contact shadows, soft area lights.

input: scene, model centre C, radius R, floor height z0 (Blender units), output size; env LEGO_EXPOSURE / LEGO_LIGHT / LEGO_FLOOR for tuning
output: world, floor and lights added to the scene; EEVEE, 24 samples, Standard view transform
pos: imported by build.py.
Why lights at 0.3 and an AO-only floor: brighter lights or a lit floor clip the backdrop and light-coloured tops to pure white.
"""
import bpy, os
from mathutils import Vector

BACK = (0.86, 0.855, 0.83)          # backdrop seen by the camera (linear); renders to about #edece9
EXPOSURE = float(os.environ.get('LEGO_EXPOSURE', '0'))
LIGHT = float(os.environ.get('LEGO_LIGHT', '0.3'))
BRIGHT = float(os.environ.get('LEGO_BRIGHT', '1.0'))
VIEW = os.environ.get('LEGO_VIEW', 'Standard')
FLOOR = float(os.environ.get('LEGO_FLOOR', '0.4'))   # contact-shadow reach, in model radii

def setup(sc, C, R, z0, W, H, lights=True):
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 24
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.view_settings.view_transform = VIEW; sc.view_settings.look = 'None'; sc.view_settings.exposure = EXPOSURE
    w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    for n in [n for n in nt.nodes if n.type != 'OUTPUT_WORLD']: nt.nodes.remove(n)
    # camera rays see the backdrop; the model only gets a low ambient so its colours keep depth
    amb = nt.nodes.new('ShaderNodeBackground'); amb.inputs[0].default_value = (*BACK, 1); amb.inputs[1].default_value = 0.35
    seen = nt.nodes.new('ShaderNodeBackground'); seen.inputs[0].default_value = (*BACK, 1); seen.inputs[1].default_value = BRIGHT
    mix = nt.nodes.new('ShaderNodeMixShader'); lp = nt.nodes.new('ShaderNodeLightPath')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(amb.outputs[0], mix.inputs[1]); nt.links.new(seen.outputs[0], mix.inputs[2])
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD'); nt.links.new(mix.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=R * 200, location=(C.x, C.y, z0 - R * 0.0015))
    # floor = the backdrop colour, unlit, darkened only by ambient occlusion: seamless horizon, soft contact shadow under the model
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True; ft = fm.node_tree
    for n in list(ft.nodes):
        if n.type != 'OUTPUT_MATERIAL': ft.nodes.remove(n)
    ao = ft.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = R * FLOOR; ao.samples = 16
    ao.inputs['Color'].default_value = (*BACK, 1)
    em = ft.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = BRIGHT
    ft.links.new(ao.outputs['Color'], em.inputs['Color'])
    ft.links.new(em.outputs[0], next(n for n in ft.nodes if n.type == 'OUTPUT_MATERIAL').inputs[0])
    bpy.context.object.data.materials.append(fm)
    if lights:
        for loc, e, s in [((0.8, -1.0, 1.6), 900, 1.6), ((-1.6, -0.6, 0.9), 300, 2.0), ((-0.2, 1.6, 1.0), 450, 1.2)]:
            L = bpy.data.objects.new('l', bpy.data.lights.new('l', 'AREA')); L.data.energy = e * R * R * LIGHT; L.data.size = R * s
            L.location = C + Vector(loc) * R * 2; L.rotation_euler = (C - L.location).to_track_quat('-Z', 'Y').to_euler()
            sc.collection.objects.link(L)
