#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle counted stitches like k10, p
    match = re.match(r'([a-zA-Z]+)(\d*)', op)
    if not match:
        return None
    
    stitch_type = match.group(1)
    count = match.group(2)
    
    if count:
        return {'type': stitch_type, 'count': int(count)}
    else:
        return {'type': stitch_type, 'count': 1}

def parse_row(row_str):
    """Parse a row string like 'k10' or 'k5 p5'"""
    # Remove comments and whitespace
    row_str = row_str.split('#')[0].strip()
    
    if not row_str:
        return []
    
    operations = []
    for op in row_str.split():
        parsed = parse_stitch_operation(op)
        if parsed:
            operations.append(parsed)
    return operations

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
    
    for line in lines:
        line = line.strip()
        if line.startswith('pattern'):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on'):
            cast_on = int(line.split()[1])
        elif line and not line.startswith('#'):
            # This is a row
            rows.append(line)
    
    # Simulate the pattern
    current_stitches = cast_on
    expanded_rows = []
    
    for i, row_str in enumerate(rows):
        # Parse row operations
        operations = parse_row(row_str)
        
        # Calculate stitch count
        start_stitches = current_stitches
        
        # For now, just simulate basic operations
        for op in operations:
            if op['type'] in ['k', 'p']:
                # Simple knit/purl - no change in stitch count
                pass
            elif op['type'] == 'k2tog':
                # Decrease by 1 stitch
                current_stitches -= 1
            elif op['type'] == 'p2tog':
                # Decrease by 1 stitch
                current_stitches -= 1
            elif op['type'] == 'bind_off':
                # This is a special case
                pass
        
        # Create expanded row
        row = {
            'expanded_row_index': i + 1,  # 1-based indexing
            'source_row': row_str,
            'instructions': operations,
            'start_stitches': start_stitches,
            'end_stitches': current_stitches
        }
        
        expanded_rows.append(row)
    
    # Check for bind_off
    bind_off = False
    for row_str in rows:
        if 'bind_off' in row_str:
            bind_off = True
            break
    
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