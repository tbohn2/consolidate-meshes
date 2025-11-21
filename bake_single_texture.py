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

# Force enable Cycles addon
if "cycles" not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module="cycles")

prefs = bpy.context.preferences.addons["cycles"].preferences

# Try environment variable override (BEST FOR BACKGROUND)
device_type = os.environ.get("CYCLES_DEVICE_TYPE", "OPTIX")
prefs.compute_device_type = device_type

# Force-enable all GPU devices
try:
    devices = prefs.devices
    for d in devices:
        d.use = True
    print("FORCED GPU ENABLED:", device_type)
except:
    print("FAILED TO ENABLE GPU, FALLING BACK TO CPU")

# Tell Cycles to use GPU
bpy.context.scene.cycles.device = "GPU"

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

    # === PREPARE RENDER SETTINGS ===
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = samples

    # Light path optimization for faster diffuse baking
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 0
    scene.cycles.volume_bounces = 0
    scene.cycles.transparent_max_bounces = 0

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

    # --- Step 1: Create new UV map and Smart UV Project ---
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

    # --- Step 2: Create new image ---
    img_name = f"{mesh_name}_bake"
    img = bpy.data.images.new(img_name, width=bake_res, height=bake_res, alpha=False)

    print(f"Blank image created")

    # --- Step 3: Add UV and Image Texture nodes to each material ---

    # Duplicate all materials with a 'temp_' prefix to ensure uniqueness
    for slot_idx, slot in enumerate(obj.material_slots):
        mat = slot.material
        if not mat or not mat.node_tree:
            continue

        unique_mat = mat.copy()
        unique_mat.name = f"temp_{mesh_name}_{mat.name}"
        obj.material_slots[slot_idx].material = unique_mat
        print(f"Created unique temporary material '{unique_mat.name}' for {mesh_name}")
                
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.node_tree:
            continue
                
        print(f"Creating nodes for {mat.name}")
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Find name of Existing Texture Node
        old_tex_node = None
        for n in nodes:
            if n.type == 'TEX_IMAGE':
                old_tex_node = n
                break

        if not old_tex_node:
            continue

        # Create UV Map node (new UV)
        uv_node = nodes.new(type='ShaderNodeUVMap')
        uv_node.uv_map = uv_name
        uv_node.label = "BakedUV"
        uv_node.location = (-600, 300)

        # Create new Image Texture node
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = img
        tex_node.label = "BakedTextureTarget"
        tex_node.location = (-400, 300)

        # Connect new UV → new Image        
        links.new(uv_node.outputs['UV'], tex_node.inputs['Vector'])

        # Connect old UV → to old texture node
        old_uv_node = nodes.new(type='ShaderNodeUVMap')
        old_uv_map_name = f"old_{mesh_name}_UV"    
        old_uv_node.uv_map = old_uv_map_name
        old_uv_node.label = f"{old_uv_map_name}_node"
        old_uv_node.location = (-1000, 300) 

        links.new(old_uv_node.outputs['UV'], old_tex_node.inputs['Vector'])

    print("Selecting new image texture nodes for baking")
    for slot_idx, slot in enumerate(obj.material_slots):
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue

        nodes = mat.node_tree.nodes
        bake_node = next((n for n in nodes if n.label == "BakedTextureTarget"), None)
        if bake_node:
            # Set this material slot as active (not strictly required for bake)
            obj.active_material_index = slot_idx
            nodes.active = bake_node
            print(f"Set BakedTextureTarget active for material '{mat.name}'")

    # --- Step 4: Bake diffuse color ---

    print("Baking Image")

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    obj.data.uv_layers.active = new_uv
                
    bpy.ops.object.bake(
        type='DIFFUSE',
        use_clear=True,
        use_selected_to_active=False,
        pass_filter={'COLOR'},
        margin=bake_margin
    )

    # Ensure image is updated after baking
    img.update()

    print("Baking complete")

    # --- Step 5: Save baked image ---
    img.save_render(filepath=os.path.join(texture_export_path, f"{mesh_name}.tif"))
    print(f"Saved baked texture to {texture_export_path}")

    # Reset save state
    bpy.ops.wm.open_mainfile(filepath=blender_file_path)

# Create new material
# for mesh_name in mesh_names:
#     # Deselect all objects
#     bpy.ops.object.select_all(action='DESELECT')

#     # Select only the target mesh
#     obj = bpy.data.objects.get(mesh_name)
#     if obj and obj.type == 'MESH':
#         obj.select_set(True)
#         bpy.context.view_layer.objects.active = obj
#     else:
#         raise Exception(f"Mesh '{mesh_name}' not found.")
    
#     # Replace materials with baked one

#     # Delete all materials 
#     obj.data.materials.clear()
#     print(f"Deleted old materials")

#     # Create new baked material
#     baked_mat = bpy.data.materials.new(name=f"{mesh_name}_Baked")
#     baked_mat.use_nodes = True
#     nodes = baked_mat.node_tree.nodes
#     links = baked_mat.node_tree.links

#     for node in nodes:
#         nodes.remove(node)

#     # Create new nodes
#     tex_node = nodes.new(type='ShaderNodeTexImage')
#     tex_node.image = img
#     bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
#     output_node = nodes.new(type='ShaderNodeOutputMaterial')

#     # Arrange nodes
#     tex_node.location = (-400, 0)
#     bsdf_node.location = (-100, 0)
#     output_node.location = (200, 0)

#     # Connect texture to base color
#     links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
#     links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

#     obj.data.materials.append(baked_mat)

#     # Target UV map name
#     old_uv_name = f"old_{mesh_name}_UV"

#     # Find and remove it
#     old_uv = obj.data.uv_layers.get(old_uv_name)
#     if old_uv:
#         obj.data.uv_layers.remove(old_uv)
#         print(f"Deleted UV map: {old_uv_name}")
#     else:
#         print(f"No UV map named '{old_uv_name}' found")

#     print(f"Replaced materials with baked texture: {mesh_name}.tif")

#     print("\n=== Baking complete! ===")

    

