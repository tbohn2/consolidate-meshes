import bpy
import os
import json
import uuid
from mathutils import Vector

def tri_area(a, b, c):
    return ((b - a).cross(c - a)).length / 2


def brush_volume(a1, a2, a3, b1, b2, b3):
    # Signed tetra volume – catches inside-out / zero-thickness
    return abs((a2 - a1).dot((a3 - a1).cross(b1 - a1))) / 6


def is_valid_brush(v1, v2, v3, v1e, v2e, v3e):
    # 1. Triangle must not be degenerate
    if tri_area(v1, v2, v3) < 0.0001:
        return False
    
    # 2. Extruded triangle must not be degenerate
    if tri_area(v1e, v2e, v3e) < 0.0001:
        return False

    # 3. Volume must be positive
    vol = brush_volume(v1, v2, v3, v1e, v2e, v3e)
    if vol < 0.0001:
        return False

    # 4. Make sure normal is not flipped or NaN
    n = (v2 - v1).cross(v3 - v1)
    if n.length < 0.0001:
        return False

    return True


SCALE = 39.37  # Blender meters → Radiant inches

def world(v, obj):
    """Convert local vertex → world space → inches."""
    v_world = obj.matrix_world @ v
    return Vector((v_world.x * SCALE, v_world.y * SCALE, v_world.z * SCALE))

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

def guid_braced_upper():
    return f"{{{str(uuid.uuid4()).upper()}}}"

def guid_plain_lower():
    return str(uuid.uuid4())

# other textures: wall_climb, dirt, grass, clip, brick, carpet, clip, cloth, concret, glass, ice, metal, mud, plaster, plastic, rock, sand, snow, stone, wood
material_type = data.get("material_type")
coll_maps_dir = data.get("coll_maps_dir")
clip = data.get("materials").get(material_type).get("full_clip")
LIGHTMAP = "lightmap_gray"
mesh_names = data.get("mesh_names")

def export_collision_map(mesh_name, filepath):
    bpy.ops.object.select_all(action='DESELECT')

    # Select only the target mesh
    obj = bpy.data.objects.get(mesh_name)
    if obj and obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    else:
        raise Exception(f"Mesh '{mesh_name}' not found.")
    
    mesh = obj.data
    mesh.calc_loop_triangles()

    brushes = []
    EXTRUDE = 0.16

    def round_vec(vec, decimals=4):
        return type(vec)([round(coord, decimals) for coord in vec])

    for i, tri in enumerate(mesh.loop_triangles):
        v1 = world(mesh.vertices[tri.vertices[0]].co, obj)
        v2 = world(mesh.vertices[tri.vertices[1]].co, obj)
        v3 = world(mesh.vertices[tri.vertices[2]].co, obj)

        normal = (v2 - v1).cross(v3 - v1).normalized()

        v1e = v1 + normal * EXTRUDE * SCALE
        v2e = v2 + normal * EXTRUDE * SCALE
        v3e = v3 + normal * EXTRUDE * SCALE

        v1 = round_vec(v1)
        v2 = round_vec(v2)
        v3 = round_vec(v3)
        v1e = round_vec(v1e)
        v2e = round_vec(v2e)
        v3e = round_vec(v3e)

        # ---- VALIDATION ----
        if not is_valid_brush(v1, v2, v3, v1e, v2e, v3e):
            print(f"Skipping invalid brush at triangle {i}")
            continue
        # ---------------------

        brush = f"""
// brush {i}
{{
 guid "{guid_braced_upper()}"
 ( {v1.x} {v1.y} {v1.z} ) ( {v2.x} {v2.y} {v2.z} ) ( {v3.x} {v3.y} {v3.z} ) {clip} 64 64 0 0 0 0 {LIGHTMAP} 16 16 0 0 0 0
 ( {v1e.x} {v1e.y} {v1e.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) {clip} 64 64 0 0 0 0 {LIGHTMAP} 16 16 0 0 0 0
 ( {v1.x} {v1.y} {v1.z} ) ( {v1e.x} {v1e.y} {v1e.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) {clip} 64 64 0 0 0 0 {LIGHTMAP} 16 16 0 0 0 0
 ( {v2.x} {v2.y} {v2.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) {clip} 64 64 0 0 0 0 {LIGHTMAP} 16 16 0 0 0 0
 ( {v3.x} {v3.y} {v3.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) ( {v1e.x} {v1e.y} {v1e.z} ) {clip} 64 64 0 0 0 0 {LIGHTMAP} 16 16 0 0 0 0
}}
    """
        brushes.append(brush)

    map_text = f"""iwmap 4
"script_startingnumber" 0
"000_Global" flags  active
"The Map" flags expanded

// entity 0
{{
guid "{guid_braced_upper()}"
"classname" "worldspawn"
"fsi" "default"
"gravity" "800"
"lodbias" "default"
"lutmaterial" "luts_t7_default"
"numOmniShadowSlices" "24"
"numSpotShadowSlices" "64"
"sky_intensity_factor0" "1"
"sky_intensity_factor1" "1"
"state_alias_1" "State 1"
"state_alias_2" "State 2"
"state_alias_3" "State 3"
"state_alias_4" "State 4"
{"".join(brushes)}
}}
// entity 1
{{
guid "{guid_braced_upper()}"
"classname" "misc_model"
"model" "{mesh_name}"
"lightingstate1" "1"
"lightingstate2" "1"
"lightingstate3" "1"
"lightingstate4" "1"
"modelscale" "1"
"static" "1"
}}
    """

    with open(filepath, "w") as f:
        f.write(map_text)

    print(f"Collision map exported to:\n{filepath}")


for mesh_name in mesh_names:
    export_collision_map(mesh_name, os.path.join(coll_maps_dir, f"{mesh_name}.map"))
