# Script to get all mesh names; copy, paste, and run in blender

print("=== Mesh Objects in this .blend file ===")

import bpy

# meshes = "["
print("[")

mesh_objs = [obj.name for obj in bpy.data.objects if obj.type == 'MESH']

for i, name in enumerate(mesh_objs):
    # meshes += f"\"{name}\""
    # if i < len(mesh_objs) - 1:
    #     meshes += ", "
    print(f"\"{name}\",") 

print("]")
# meshes += "]"

# print(meshes)