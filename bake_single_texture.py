import os
import subprocess
import json

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

get_mesh_names_script_path = data.get("get_mesh_names_script_path")
blender_exe_path = data.get("blender_exe_path")
blender_file_path = data.get("blender_file_path")
combine_materials_script_path = data.get("combine_materials_script_path")
export_xmodel_script_path = data.get("export_xmodel_script_path")

env = os.environ.copy()
env["CYCLES_DEVICE_TYPE"] = "OPTIX"

cmd = [
    blender_exe_path,
    "--background", blender_file_path,
    "--python", get_mesh_names_script_path      # Use to get all mesh names
    # "--python", combine_materials_script_path
]

subprocess.run(cmd, env=env)

# Execute script to export each mesh as xmodel
cmd = [
    blender_exe_path,
    "--background", blender_file_path,
    "--python", export_xmodel_script_path
]

subprocess.run(cmd, env=env)