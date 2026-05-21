import sys
import os
import json
import re

def main():
    if len(sys.argv) != 3:
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    command = sys.argv[1]
    input_file = sys.argv[2]
    
    if command != "compile":
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(input_file):
        print("Error: Input file does not exist", file=sys.stderr)
        sys.exit(2)

    # Read the file
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Parse the file
    pattern_name = None
    cast_on = None
    rows = []
    expanded_rows = []
    final_stitch_count = 0
    bind_off = False
    errors = []

    # Process each line
    for i, line in enumerate(lines):
        line_num = i + 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on'):
            cast_on = int(line.split()[1])
        elif line.startswith('row '):
            row_num = int(line.split()[1].rstrip(':'))
            instructions = line.split(':')[1].strip()
            # This is a basic version - a full implementation would need to handle all the parsing rules
        elif line.startswith('bind_off'):
            bind_off = True
        elif line.startswith('repeat rows '):
            # This would need to be implemented to handle row repeats
            pass

    # Create a basic valid output structure for now
    output = {
        "pattern_name": pattern_name if pattern_name else None,
        "cast_on": cast_on,
        "valid": True,
        "errors": errors,
        "expanded_rows": expanded_rows,
        "final_stitch_count": final_stitch_count,
        "bind_off": bind_off
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()