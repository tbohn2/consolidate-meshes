# For each mesh:
# Assign any material or texture with ".00" to the name without ".00" and delete the ".00"
#   duplicate then save
# Export the xmodel
# Export textures
# Write .gdt data for xmodel, each material, and texture

import bpy
import os
import sys
import json
import re

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

blender_file_path = data.get("blender_file_path")
xmodel_export_path = data.get("xmodel_export_path")
mesh_names = data.get("mesh_names")
texture_export_path = data.get("texture_export_path")

SUFFIX_RE = re.compile(r"\.\d+$")

def base_name(name):
    """Strip numeric suffix (.00, .001, etc.)"""
    return SUFFIX_RE.sub("", name)

for mesh_name in mesh_names:
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select only the target mesh
    obj = bpy.data.objects.get(mesh_name)
    if obj and obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    else:
        raise Exception(f"Mesh '{mesh_name}' not found.")
        
    # -------------------------
    # MATERIAL FIX
    # -------------------------
        
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue

            clean_name = base_name(mat.name)

            if mat.name != clean_name and clean_name in bpy.data.materials:
                original = bpy.data.materials[clean_name]

                print(f"Reassigning material: {mat.name} -> {original.name}")
                slot.material = original

               # Remove duplicate if unused
                if mat.users == 0:
                   bpy.data.materials.remove(mat)


    # -------------------------
    # IMAGE TEXTURE FIX
    # -------------------------
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                img = node.image
                clean_name = base_name(img.name)

                if img.name != clean_name and clean_name in bpy.data.images:
                    original = bpy.data.images[clean_name]

                    print(f"Reassigning image: {img.name} -> {original.name}")
                    node.image = original

                    if img.users == 0:
                        bpy.data.images.remove(img)


    # -------------------------
    # SAVE FILE
    # -------------------------
    bpy.ops.wm.save_mainfile()

    print("Material and texture cleanup complete.")

    
    

