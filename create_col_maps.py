import bpy
import os
import json
# from mathutils import Vector

# SCALE = 39.37  # Blender meters → Radiant inches

# def world(v, obj):
#     """Convert local vertex → world space → inches."""
#     v_world = obj.matrix_world @ v
#     return Vector((v_world.x * SCALE, v_world.y * SCALE, v_world.z * SCALE))

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

OUTPUT_DIR = r"D:\SteamLibrary\steamapps\common\Call of Duty Black Ops III\share\raw\collmaps"
BRUSH_CONTENTS = "clip_physics"
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

    for i, tri in enumerate(mesh.loop_triangles):
        # Get vertex coordinates
        v1 = mesh.vertices[tri.vertices[0]].co
        v2 = mesh.vertices[tri.vertices[1]].co
        v3 = mesh.vertices[tri.vertices[2]].co

        normal = (v2 - v1).cross(v3 - v1).normalized()

        # Extruded top vertices
        v1e = v1 + normal * EXTRUDE
        v2e = v2 + normal * EXTRUDE
        v3e = v3 + normal * EXTRUDE

        # Build a single triangle brush
        # Radiant wants brushes with 6 faces. For a triangle,
        # we create a tetrahedron-style minimal convex hull.
        brush = f"""// brush {i}
    {{
    ( {v1.x} {v1.y} {v1.z} ) ( {v2.x} {v2.y} {v2.z} ) ( {v3.x} {v3.y} {v3.z} ) {BRUSH_CONTENTS} 0 0 0 0 0 0 {LIGHTMAP} 0 0 0
    ( {v1e.x} {v1e.y} {v1e.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) {BRUSH_CONTENTS} 0 0 0 0 0 0 {LIGHTMAP} 0 0 0

    ( {v1.x} {v1.y} {v1.z} ) ( {v1e.x} {v1e.y} {v1e.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) {BRUSH_CONTENTS} 0 0 0 0 0 0 {LIGHTMAP} 0 0 0
    ( {v2.x} {v2.y} {v2.z} ) ( {v2e.x} {v2e.y} {v2e.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) {BRUSH_CONTENTS} 0 0 0 0 0 0 {LIGHTMAP} 0 0 0
    ( {v3.x} {v3.y} {v3.z} ) ( {v3e.x} {v3e.y} {v3e.z} ) ( {v1e.x} {v1e.y} {v1e.z} ) {BRUSH_CONTENTS} 0 0 0 0 0 0 {LIGHTMAP} 0 0 0
    }}
    """
        brushes.append(brush)

    map_text = f"""iwmap 4
    "000_Global" flags  active
    "The Map" flags

    // entity 0
    {{
    "classname" "worldspawn"
    {"".join(brushes)}
    }}
    // entity 1
    {{
    "origin" "0.0 0.0 0.0"
    "model" "{mesh_name}"
    "classname" "misc_model"
    }}
    """

    with open(filepath, "w") as f:
        f.write(map_text)

    print(f"Collision map exported to:\n{filepath}")


for mesh_name in mesh_names:
    export_collision_map(mesh_name, os.path.join(OUTPUT_DIR, f"{mesh_name}.map"))
