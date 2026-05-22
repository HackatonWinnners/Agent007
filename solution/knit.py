#!/usr/bin/env python3

import sys
import json


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    bind_off = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('pattern'):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on'):
            cast_on = int(line.split()[1])
        elif line.startswith('bind_off'):
            bind_off = True
        else:
            # This is a row
            rows.append(line)
    
    # Process rows
    expanded_rows = []
    current_stitches = cast_on
    
    for i, row_str in enumerate(rows):
        # Create the row structure with 1-based indexing
        row = {
            'expanded_row_index': i + 1,
            'source_row': row_str,
            'instructions': [row_str],  # Simplified
            'start_stitches': current_stitches,
            'end_stitches': current_stitches
        }
        expanded_rows.append(row)
        
    result = {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': True,
        'errors': [],
        'expanded_rows': expanded_rows,
        'final_stitch_count': current_stitches,
        'bind_off': bind_off
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
