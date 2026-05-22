#!/usr/bin/env python3

import sys
import json
import re

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    errors = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('pattern'):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on'):
            try:
                cast_on = int(line.split()[1])
            except (ValueError, IndexError):
                errors.append(f"Invalid cast_on value on line {i+1}")
        elif line.startswith('row'):
            try:
                # Parse row definition
                row_def = line[3:].strip()
                # Handle bracketed repeats like: [k1, p1] x2
                if '[' in row_def and ']' in row_def and 'x' in row_def:
                    # Extract bracketed content and repeat count
                    match = re.match(r'\[(.*)\]\s*x\s*(\d+)', row_def)
                    if match:
                        content = match.group(1)
                        repeat_count = int(match.group(2))
                        # Split content by comma and repeat
                        stitches = [s.strip() for s in content.split(',')]
                        expanded_row = stitches * repeat_count
                        rows.append(expanded_row)
                    else:
                        errors.append(f"Invalid bracket repeat format on line {i+1}")
                else:
                    # Regular row definition
                    stitches = [s.strip() for s in row_def.split(',')]
                    rows.append(stitches)
            except Exception as e:
                errors.append(f"Error parsing row on line {i+1}: {str(e)}")
    
    return pattern_name, cast_on, rows, errors

def simulate_stitch_counts(rows, cast_on):
    stitch_count = cast_on
    expanded_rows = []
    
    for row in rows:
        # Expand the row
        expanded_row = []
        for stitch in row:
            if stitch.startswith('k') or stitch.startswith('p'):
                expanded_row.append(stitch)
            elif stitch.startswith('k') or stitch.startswith('p'):
                expanded_row.append(stitch)
        expanded_rows.append(expanded_row)
        
        # Count stitches in this row
        for stitch in row:
            if stitch.startswith('k') or stitch.startswith('p'):
                stitch_count += 1  # Simplified for now
    
    return expanded_rows, stitch_count


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        pattern_name, cast_on, rows, errors = parse_knit_file(input_file)
        
        # If there are errors, return them
        if errors:
            result = {
                'pattern_name': pattern_name,
                'cast_on': cast_on,
                'valid': False,
                'errors': errors,
                'expanded_rows': [],
                'final_stitch_count': cast_on,
                'bind_off': False
            }
            print(json.dumps(result))
            sys.exit(1)
        
        # Simulate stitch counts
        expanded_rows, final_stitch_count = simulate_stitch_counts(rows, cast_on)
        
        # Check if we should bind off (simplified logic)
        bind_off = False
        if len(rows) > 0:
            bind_off = True  # Simplified
        
        result = {
            'pattern_name': pattern_name,
            'cast_on': cast_on,
            'valid': True,
            'errors': [],
            'expanded_rows': expanded_rows,
            'final_stitch_count': final_stitch_count,
            'bind_off': bind_off
        }
        
        print(json.dumps(result))
        
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()