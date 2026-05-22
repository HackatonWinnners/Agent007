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

def parse_row(row):
    """Parse a row of stitches"""
    # Remove comments and split by space
    row = row.split('#')[0].strip()
    if not row:
        return []
    
    operations = []
    for op in row.split():
        parsed = parse_stitch_operation(op)
        if parsed:
            operations.append(parsed)
    return operations

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print('Usage: python3 knit.py compile <input_file>', file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print('Error: File not found', file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    bind_off = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('pattern'):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on'):
            cast_on = int(line.split()[1])
        elif line.startswith('bind_off'):
            bind_off = True
        elif line.startswith('row'):
            # Parse row definition
            row_content = line.split(' ', 1)[1] if len(line.split()) > 1 else ''
            rows.append(row_content)
    
    # Process rows
    expanded_rows = []
    current_stitches = cast_on
    
    # For now, just return the rows as-is
    for i, row_content in enumerate(rows):
        operations = parse_row(row_content)
        row = {
            'expanded_row_index': i + 1,  # 1-based indexing
            'source_row': row_content,
            'instructions': [op['type'] + (str(op['count']) if op['count'] > 1 else '') for op in operations],
            'start_stitches': current_stitches,
            'end_stitches': current_stitches  # Simplified for now
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
