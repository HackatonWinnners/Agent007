#!/usr/bin/env python3

import sys
import json
import re

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    errors = []
    
    for line in lines:
        if line.startswith('pattern "'):
            pattern_name = line.split('pattern "', 1)[1].rsplit('"', 1)[0]
        elif line.startswith('cast_on '):
            cast_on = int(line.split('cast_on ')[1])
        elif line.startswith('row '):
            # Parse row definition
            row_match = re.match(r'row ([0-9]+):\s*(.*)', line)
            if row_match:
                row_num = int(row_match.group(1))
                row_content = row_match.group(2)
                rows.append((row_num, row_content))
    
    # Process rows to expand repeats
    expanded_rows = []
    current_stitch_count = cast_on
    
    for row_num, row_content in rows:
        # Handle bracketed repeats
        expanded_content = expand_brackets(row_content)
        
        # Count stitches in expanded content
        stitch_count = count_stitches(expanded_content)
        
        # Create expanded row structure
        expanded_row = {
            "start_stitches": current_stitch_count,
            "end_stitches": current_stitch_count + stitch_count,
            "expanded_row_index": len(expanded_rows),
            "source_row": row_num,
            "instructions": expanded_content
        }
        
        expanded_rows.append(expanded_row)
        current_stitch_count += stitch_count
    
    # Determine bind_off
    bind_off = False
    if rows:
        bind_off = True  # Simple heuristic - if there are rows, bind off
    
    return {
        "pattern_name": pattern_name,
        "cast_on": cast_on,
        "valid": len(errors) == 0,
        "errors": errors,
        "expanded_rows": expanded_rows,
        "final_stitch_count": current_stitch_count,
        "bind_off": bind_off
    }

def expand_brackets(content):
    # Simple bracket expansion
    # Example: [k1, p1] x2 becomes k1, p1, k1, p1
    bracket_pattern = r'\[([^\]]+)\]\s*x(\d+)'
    while re.search(bracket_pattern, content):
        match = re.search(bracket_pattern, content)
        if match:
            inner_content = match.group(1)
            repeat_count = int(match.group(2))
            expanded = (inner_content + ", ") * repeat_count
            expanded = expanded.rstrip(", ")
            content = content[:match.start()] + expanded + content[match.end():]
    return content

def count_stitches(content):
    # Simple stitch counting
    stitches = 0
    # Count each stitch instruction
    for item in content.split(", "):
        item = item.strip()
        if item.startswith("k") or item.startswith("p"):
            # For simplicity, assume each stitch instruction adds 1 stitch
            stitches += 1
    return stitches

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        result = parse_knit_file(input_file)
        print(json.dumps(result))
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
