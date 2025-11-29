import bpy
import os
import sys
import json

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

blender_file_path = data.get("blender_file_path")
xmodel_export_path = data.get("xmodel_export_path")
mesh_names = data.get("mesh_names")
texture_export_path = data.get("texture_export_path")
bake_res = data.get("bake_res")
island_margin = data.get("island_margin")
bake_margin = data.get("bake_margin")
samples = data.get("samples")

def get_materials():
    # Bake textures to one texture
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

        # Get the active/selected mesh object
        obj = bpy.context.active_object
        if not obj or obj.type != 'MESH':
            # Try to get first selected mesh
            selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']
            if not selected_meshes:
                raise Exception("No mesh object selected. Please select a mesh object.")
            obj = selected_meshes[0]

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_name = obj.name

        print(f"\n=== Processing {mesh_name} ===")

        # Rename existing UV map
        if obj.data.uv_layers:
            for uv in obj.data.uv_layers:
                old_name = uv.name
                new_name = f"old_{obj.name}_UV"
                uv.name = new_name
                print(f"Renamed '{old_name}' → '{new_name}' for {obj.name}")

        # --- Create new UV map and Smart UV Project ---
        uv_name = f"{mesh_name}_UV"
        new_uv = obj.data.uv_layers.new(name=uv_name)
        # Set it as the active UV map
        obj.data.uv_layers.active = new_uv

        print(f"Created new UV map: {new_uv.name}")

        # --- Smart UV Project ---
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=island_margin)
        print(f"Completed new Smart UV Project")

        bpy.ops.object.mode_set(mode='OBJECT')        
        
        # Replace materials with baked one

        # Delete all materials 
        obj.data.materials.clear()
        print(f"Deleted old materials")

        # Create new baked material
        baked_mat = bpy.data.materials.new(name=f"{mesh_name}_Baked")
        baked_mat.use_nodes = True
        nodes = baked_mat.node_tree.nodes
        links = baked_mat.node_tree.links

        for node in nodes:
            nodes.remove(node)

        # Create new nodes
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = texture_export_path
        bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        output_node = nodes.new(type='ShaderNodeOutputMaterial')

        # Arrange nodes
        tex_node.location = (-400, 0)
        bsdf_node.location = (-100, 0)
        output_node.location = (200, 0)

        # Connect texture to base color
        links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
        links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

        obj.data.materials.append(baked_mat)

        # Target UV map name
        old_uv_name = f"old_{mesh_name}_UV"

        # Find and remove it
        old_uv = obj.data.uv_layers.get(old_uv_name)
        if old_uv:
            obj.data.uv_layers.remove(old_uv)
            print(f"Deleted UV map: {old_uv_name}")
        else:
            print(f"No UV map named '{old_uv_name}' found")

        print(f"Replaced materials with baked texture: {mesh_name}.tif")       