import os
import json
import re

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

coll_maps_dir = data.get("coll_maps_dir")
invalid_brushes = data.get("invalid_brushes", [])


def remove_brushes(text, brushes_to_remove):
    lines = text.splitlines(keepends=True)
    result = []
    skip = False

    for line in lines:
        if not skip:
            # Check if this line is the start of a brush we want to remove
            for brush in brushes_to_remove:
                if line.strip() == f"// brush {brush}":
                    skip = True
                    print(f"Removing brush {brush}")
                    break
            else:
                result.append(line)
        else:
            if line.strip() == "}":
                skip = False 
                continue

    return "".join(result)

    


for entry in invalid_brushes:
    mesh = entry.get("mesh")
    brushes_to_remove = entry.get("brushes", [])

    if not mesh or not brushes_to_remove:
        continue

    map_path = os.path.join(coll_maps_dir, f"{mesh}.map")

    if not os.path.exists(map_path):
        print(f"Map not found: {map_path}")
        continue

    print(f"Processing: {map_path}")

    with open(map_path, "r") as f:
        text = f.read()

    cleaned = remove_brushes(text, brushes_to_remove)

    with open(map_path, "w") as f:
        f.write(cleaned)

    print(f"Saved cleaned file for {mesh}")
