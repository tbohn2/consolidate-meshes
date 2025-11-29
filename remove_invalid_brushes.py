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
    brushes_to_remove = set(str(b) for b in brushes_to_remove)

    out = []
    skipping = False
    brace_depth = 0
    current_target = None

    i = 0
    while i < len(lines):
        line = lines[i]

        if not skipping:
            # Detect "// brush N"
            stripped = line.strip()
            if stripped.startswith("// brush"):
                parts = stripped.split()
                if len(parts) >= 3:
                    bn = parts[2]
                    if bn in brushes_to_remove:
                        print(f"Removing brush {bn}")
                        skipping = True
                        current_target = bn
                        brace_depth = 0
                        i += 1
                        continue  # do not copy this line
        else:
            # While skipping, track braces to know when the block ends
            brace_depth += line.count("{")
            brace_depth -= line.count("}")

            # Did the brush block end?
            if brace_depth <= 0 and "}" in line:
                skipping = False
                current_target = None
                i += 1
                continue  # skip the closing line as well

            # Still inside the block → skip the line
            i += 1
            continue

        # Not skipping → keep line
        out.append(line)
        i += 1

    return "".join(out)


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
