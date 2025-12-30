import bpy
import os
import json

# ============================
# CONFIG
# ============================
script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

blender_file_path = data.get("blender_file_path")
mesh_names = data.get("mesh_names")
texture_export_path = data.get("texture_export_path")

exported_images = set()


def export_image(image):
    """Save image to export directory if not already exported"""
    if not image.filepath:
        return

    name = bpy.path.clean_name(image.name).lower()
    export_path = os.path.join(texture_export_path, name + ".tif")

    if export_path in exported_images:
        return

    try:
        image.save_render(export_path)
        exported_images.add(export_path)
        print(f"Exported: {export_path}")
    except Exception as e:
        print(f"Failed to export {image.name}: {e}")


# ============================
# MAIN
# ============================
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
    
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    export_image(node.image)


print("Texture export complete.")
