import json
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(script_dir, "data.json")

with open(json_path, "r") as f:
    data = json.load(f)

gdt_path = data.get("gdt_path")

def remove_duplicate_blocks(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    seen_headers = set()
    output_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect header line:  "name" ( "type" )
        if line.strip().startswith('"') and '(' in line and ')' in line:
            header = line.strip()

            # Expect next non-empty line to be "{"
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            if j < len(lines) and lines[j].strip() == "{":
                if header in seen_headers:
                    # Skip this entire block
                    brace_depth = 0
                    i = j
                    while i < len(lines):
                        if "{" in lines[i]:
                            brace_depth += 1
                        if "}" in lines[i]:
                            brace_depth -= 1
                            if brace_depth == 0:
                                i += 1
                                break
                        i += 1
                    continue
                else:
                    seen_headers.add(header)

        output_lines.append(line)
        i += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)


# Example usage
remove_duplicate_blocks(
    input_path=gdt_path,
    output_path="output_deduped.gdt"
)
