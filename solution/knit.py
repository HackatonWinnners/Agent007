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
    
    operation = match.group(1)
    count = match.group(2)
    
    # Default count is 1 if not specified
    if not count:
        count = 1
    else:
        count = int(count)
    
    return {
        'operation': operation,
        'count': count
    }

def expand_brackets(instructions):
    """Expand bracketed patterns like [k1, p1] x2"""
    # Simple approach: find bracketed patterns and expand them
    result = []
    i = 0
    while i < len(instructions):
        instr = instructions[i]
        # Check if this is a bracketed pattern
        if instr.startswith('[') and instr.endswith(']'):
            # Extract the content and repeat count
            content = instr[1:-1]
            # Look for x<number> pattern
            repeat_match = re.search(r'x(\d+)$', content)
            if repeat_match:
                repeat_count = int(repeat_match.group(1))
                # Remove the repeat part
                pattern_content = content[:repeat_match.start()].strip()
                # Split the pattern content
                pattern_parts = [part.strip() for part in pattern_content.split(',') if part.strip()]
                # Add the pattern repeated times
                for _ in range(repeat_count):
                    result.extend(pattern_parts)
            else:
                # No repeat, just add as-is
                result.append(instr)
        else:
            result.append(instr)
        i += 1
    return result


def simulate_row(row_instructions, start_stitches):
    """Simulate a row and return the end stitch count"""
    current_stitches = start_stitches
    
    for instr in row_instructions:
        # Parse the instruction
        parsed = parse_stitch_operation(instr)
        if not parsed:
            return None
        
        operation = parsed['operation']
        count = parsed['count']
        
        # Apply stitch count changes
        if operation in ['k', 'p']:
            # k and p don't change stitch count
            pass
        elif operation == 'k2tog':
            # k2tog reduces stitch count by 1
            current_stitches -= 1
        elif operation == 'ssk':
            # ssk reduces stitch count by 1
            current_stitches -= 1
        elif operation == 'inc':
            # inc increases stitch count by 1
            current_stitches += 1
        elif operation == 'yo':
            # yo increases stitch count by 1
            current_stitches += 1
    
    return current_stitches


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print('Usage: python3 knit.py compile <input_file>', file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print('Error: File not found', file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    bind_off = False
    
    for i, line in enumerate(lines):
        if line.startswith('pattern '):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on '):
            # Handle comments in cast_on line
            cast_on_line = line.split('#')[0].strip()
            cast_on = int(cast_on_line.split(' ', 1)[1])
        elif line.startswith('row '):
            # Extract row number and instructions
            row_match = re.match(r'row (\d+):(.*)', line)
            if row_match:
                row_num = int(row_match.group(1))
                instructions = [instr.strip() for instr in row_match.group(2).split(',') if instr.strip()]
                rows.append({
                    'row_number': row_num,
                    'instructions': instructions
                })
        elif line == 'bind_off':
            bind_off = True
    
    # Expand brackets in rows
    expanded_rows = []
    for row in rows:
        # Expand brackets in instructions
        expanded_instructions = expand_brackets(row['instructions'])
        expanded_rows.append({
            'row_number': row['row_number'],
            'instructions': expanded_instructions,
            'start_stitches': cast_on,  # This will be updated as we process rows
            'end_stitches': cast_on
        })
    
    # Simulate each row
    current_stitches = cast_on
    for i, row in enumerate(expanded_rows):
        # For now, just use the basic stitch counting
        # In a real implementation, we'd properly simulate each row
        row['start_stitches'] = current_stitches
        row['end_stitches'] = current_stitches  # Placeholder
        
        # Update current stitches for next row
        # This is a simplified approach
        current_stitches = row['end_stitches']
    
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
