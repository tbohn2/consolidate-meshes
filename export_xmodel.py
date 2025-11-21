import bpy
import os
import sys
import json

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

xmodel_export_path = data.get("xmodel_export_path")
mesh_names = data.get("mesh_names")

print("\nFlipping Normals")
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

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')   # select all faces
    bpy.ops.mesh.flip_normals()                # invert normals
    bpy.ops.object.mode_set(mode='OBJECT')

    # Export as xmodel
    addon_name = "_pv_blender_cod"  # exact module name of the addon

    # Check if addon is enabled
    if not addon_name in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=addon_name)
        print(f"Enabled addon: {addon_name}")
    else:
        print(f"Addon already enabled: {addon_name}")

    format = "xmodel_bin"
    xmodel_filepath = rf"{xmodel_export_path}\{mesh_name}.{format}"

    bpy.ops.export_scene.xmodel(
        filepath=xmodel_filepath,
        use_selection=True,       # Export only selected objects
        apply_modifiers=True,     # Apply modifiers before export
        target_format=format
    )

    print (f"Exported {mesh_name} successfully")

print ("Exported all models successfully")