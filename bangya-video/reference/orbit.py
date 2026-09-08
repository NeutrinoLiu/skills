# -*- coding: utf-8 -*-
"""Turntable renders of the Mani4D meshes, for the cuts that talk about 3D.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P build/orbit.py -- SEQ MODE OUT

A static picture of a mesh cannot show what "the back of the object" means, and it cannot
show that a coordinate map keeps its colour as the object turns. So the 3D content is
rendered as a 4-second seamless orbit instead.

MODE is one of
    tex     the textured mesh as reconstructed
    rcm     the relative coordinate map — colour is position in the object's bounding box,
            which is exactly Blender's "Generated" texture coordinate
    white   the untextured shell, for the pipeline step where only geometry exists

Driven by build/orbits.py, which calls this once per clip and muxes the frames with ffmpeg.
"""
import math
import os
import sys

import bpy

FRAMES = int(os.environ.get("ORBIT_FRAMES", 120))    # 4 s at 30 fps; 1 to test a look
RES = 640
BG = (0.945, 0.937, 0.918)           # --band #F1EFEA — the backdrop, added after the render


def to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(seq_dir):
    bpy.ops.wm.obj_import(filepath=os.path.join(seq_dir, "mesh", "scaled_mesh.obj"))
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def frame_up(meshes):
    """Centre the meshes on the origin and scale the lot into a unit cube."""
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ __import__("mathutils").Vector(c)
            for i in range(3):
                lo[i], hi[i] = min(lo[i], w[i]), max(hi[i], w[i])
    mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
    span = max(hi[i] - lo[i] for i in range(3)) or 1.0

    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.collection.objects.link(pivot)
    for o in meshes:
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
        o.location = (o.location[0] - mid[0], o.location[1] - mid[1], o.location[2] - mid[2])
    pivot.scale = (1 / span,) * 3
    return pivot


def emission(name, tex_node):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    tex_node(nt, em)
    return m


def rcm_material():
    def wire(nt, em):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        # "Generated" is the vertex position normalised into the object's own bounding box,
        # which is the definition of a relative coordinate map.
        nt.links.new(tc.outputs["Generated"], em.inputs["Color"])
    return emission("rcm", wire)


def white_material():
    m = bpy.data.materials.new("white")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    # a light clay, not white: on the deck's cream band a white shell has no edge at all
    b.inputs["Base Color"].default_value = (0.62, 0.62, 0.615, 1)
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Metallic"].default_value = 0.0
    return m


def override(meshes, mat):
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(mat)


def light_and_camera(elev_deg, dist, raw):
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    # The film is transparent and the panel colour is composited afterwards, so the world
    # here is only a fill light — its strength is free to be whatever flatters the shell.
    bg.inputs[0].default_value = (*tuple(map(to_linear, BG)), 1.0)
    bg.inputs[1].default_value = 0.55
    bpy.context.scene.world = world

    for name, energy, loc, rot in (
            ("key", 55, (2.4, -2.4, 3.0), (0.7, 0.0, 0.79)),
            ("fill", 18, (-2.8, -1.6, 0.9), (1.35, 0.0, -1.05))):
        lt = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        lt.data.energy, lt.data.size = energy, 4.0
        lt.location, lt.rotation_euler = loc, rot
        bpy.context.collection.objects.link(lt)

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 62
    e = math.radians(elev_deg)
    cam.location = (0, -dist * math.cos(e), dist * math.sin(e))
    cam.rotation_euler = (math.pi / 2 - e, 0, 0)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam


def spin(pivot):
    """One full turn over FRAMES+1, rendering FRAMES of it, so the loop is seamless."""
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, 2 * math.pi)
    pivot.keyframe_insert("rotation_euler", frame=FRAMES + 1)
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def main():
    seq_dir, mode, out = sys.argv[sys.argv.index("--") + 1:][:3]
    clear()
    meshes = load(seq_dir)
    if mode == "rcm":
        override(meshes, rcm_material())
    elif mode == "white":
        override(meshes, white_material())
    pivot = frame_up(meshes)
    raw = mode == "rcm"
    light_and_camera(elev_deg=14, dist=2.05, raw=raw)
    spin(pivot)

    sc = bpy.context.scene
    # Standard, not Blender's default AgX: the deck's flat palette must come out as authored.
    # The coordinate map goes further and renders Raw, so a pixel's colour is literally the
    # point's position in the bounding box, the way the dataset stores it.
    sc.view_settings.view_transform = "Raw" if raw else "Standard"
    sc.view_settings.look = "None"
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 24
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = out
    sc.frame_start, sc.frame_end = 1, FRAMES
    bpy.ops.render.render(animation=True)


main()
