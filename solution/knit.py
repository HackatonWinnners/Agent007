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
        return (stitch_type, int(count))
    else:
        return (stitch_type, 1)

def parse_row(row_str):
    """Parse a row string into instructions"""
    # Remove comments and split by space
    row_str = row_str.split('#')[0].strip()
    if not row_str:
        return []
    
    instructions = []
    for op in row_str.split():
        parsed = parse_stitch_operation(op)
        if parsed:
            instructions.append(parsed)
    return instructions

def simulate_stitch_count(instructions, start_stitches):
    """Simulate stitch count changes for a row"""
    current_stitches = start_stitches
    
    for stitch_type, count in instructions:
        if stitch_type in ['k', 'p', 'yo']:
            # Knit and purl increase stitch count
            current_stitches += count
        elif stitch_type == 'k2tog':
            # Knit two together decreases stitch count
            current_stitches -= 1
        elif stitch_type == 'p2tog':
            # Purl two together decreases stitch count
            current_stitches -= 1
        elif stitch_type == 's2k':
            # Slip 2 knit decreases stitch count
            current_stitches -= 1
        elif stitch_type == 's2p':
            # Slip 2 purl decreases stitch count
            current_stitches -= 1
        elif stitch_type == 'm1':
            # Make one increases stitch count
            current_stitches += 1
        elif stitch_type == 'm1l':
            # Make one left increases stitch count
            current_stitches += 1
        elif stitch_type == 'm1r':
            # Make one right increases stitch count
            current_stitches += 1
        elif stitch_type == 'ssk':
            # Slip, slip, knit decreases stitch count
            current_stitches -= 1
        elif stitch_type == 'kfb':
            # Knit front and back increases stitch count
            current_stitches += 1
        elif stitch_type == 'pfb':
            # Purl front and back increases stitch count
            current_stitches += 1
        elif stitch_type == 'sl':
            # Slip decreases stitch count
            current_stitches -= 1
        elif stitch_type == 'bind_off':
            # Bind off decreases stitch count
            current_stitches -= 1
    
    return current_stitches

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
        instructions = parse_row(row_str)
        start_stitches = current_stitches
        end_stitches = simulate_stitch_count(instructions, start_stitches)
        current_stitches = end_stitches
        
        # Create the row structure
        row = {
            'expanded_row_index': i + 1,  # 1-based indexing
            'source_row': row_str,
            'instructions': [f'{op[0]}{op[1]}' if op[1] > 1 else op[0] for op in instructions],
            'start_stitches': start_stitches,
            'end_stitches': end_stitches
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
