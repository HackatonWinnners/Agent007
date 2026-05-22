#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle counted stitches like k10, p
    match = re.match(r'^(k|p|yo|k2tog|ssk|inc|dec|sl1|rep|bind_off|cast_on)(\d*)$', op)
    if not match:
        return None
    
    operation = match.group(1)
    count = int(match.group(2)) if match.group(2) else 1
    
    return {
        'operation': operation,
        'count': count
    }

def expand_brackets(instructions):
    """Expand bracketed patterns like [k1, p1] x2"""
    result = []
    i = 0
    while i < len(instructions):
        instr = instructions[i]
        # Check if this is a bracketed pattern
        if isinstance(instr, str) and instr.startswith('[') and instr.endswith(']'):
            # Extract the content and repeat count
            bracket_content = instr[1:-1]  # Remove brackets
            # Look for xN pattern
            repeat_match = re.search(r'x(\d+)$', bracket_content)
            if repeat_match:
                repeat_count = int(repeat_match.group(1))
                # Remove the xN part from content
                content = bracket_content[:repeat_match.start()].strip()
                # Split the content by comma
                inner_instructions = [x.strip() for x in content.split(',') if x.strip()]
                # Expand the pattern
                for _ in range(repeat_count):
                    result.extend(inner_instructions)
            else:
                # No repeat, just add the content
                result.append(instr)
        else:
            result.append(instr)
        i += 1
    return result

def simulate_row(row_instructions, start_stitches):
    """Simulate a row and return the stitch count changes"""
    current_stitches = start_stitches
    instructions = []
    
    for instr in row_instructions:
        if isinstance(instr, str):
            # This is a stitch operation
            parsed = parse_stitch_operation(instr)
            if parsed:
                operation = parsed['operation']
                count = parsed['count']
                
                # Calculate stitch change
                if operation in ['k', 'p']:
                    # These don't change stitch count
                    stitch_change = 0
                elif operation in ['k2tog', 'ssk']:
                    # These reduce stitch count by 1
                    stitch_change = -1
                elif operation in ['inc']:
                    # These increase stitch count by 1
                    stitch_change = 1
                elif operation in ['yo']:
                    # These increase stitch count by 1
                    stitch_change = 1
                else:
                    # Default to no change
                    stitch_change = 0
                
                # Add instruction with stitch change
                instructions.append({
                    'operation': operation,
                    'count': count,
                    'stitch_change': stitch_change
                })
                
                # Update current stitch count
                current_stitches += stitch_change * count
            else:
                # Invalid operation
                return None, f"Invalid stitch operation: {instr}"
        else:
            # Already parsed instruction
            instructions.append(instr)
            
    return instructions, current_stitches

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = [line.rstrip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.", file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Untitled"
    cast_on = 0
    rows = []
    bind_off = False
    errors = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('pattern '):
            pattern_name = line[8:].strip('"')
        elif line.startswith('cast_on '):
            try:
                cast_on = int(line[8:])
            except ValueError:
                errors.append({
                    'type': 'error',
                    'code': 'INVALID_CAST_ON',
                    'message': f'Invalid cast_on value: {line[8:]}',
                    'line': i + 1
                })
        elif line.startswith('row '):
            # Parse row definition
            row_match = re.match(r'row (\d+):\s*(.*)', line)
            if row_match:
                row_num = int(row_match.group(1))
                row_content = row_match.group(2)
                
                # Split by comma to get individual instructions
                instructions = [instr.strip() for instr in row_content.split(',') if instr.strip()]
                
                # Expand brackets
                expanded_instructions = expand_brackets(instructions)
                
                rows.append({
                    'row': row_num,
                    'instructions': expanded_instructions
                })
            else:
                errors.append({
                    'type': 'error',
                    'code': 'INVALID_ROW',
                    'message': f'Invalid row definition: {line}',
                    'line': i + 1
                })
        elif line == 'bind_off':
            bind_off = True
        
    # Validate that we have a pattern name and cast_on
    if not pattern_name or cast_on == 0:
        errors.append({
            'type': 'error',
            'code': 'MISSING_PATTERN_OR_CAST_ON',
            'message': 'Pattern name and cast_on are required',
            'line': 1
        })
    
    # Simulate rows
    expanded_rows = []
    current_stitches = cast_on
    
    for row in rows:
        row_num = row['row']
        instructions = row['instructions']
        
        # Simulate this row
        simulated_instructions, end_stitches = simulate_row(instructions, current_stitches)
        
        if simulated_instructions is None:
            errors.append({
                'type': 'error',
                'code': 'ROW_SIMULATION_ERROR',
                'message': end_stitches,
                'line': row_num
            })
        else:
            expanded_rows.append({
                'row': row_num,
                'instructions': simulated_instructions,
                'start_stitches': current_stitches,
                'end_stitches': end_stitches
            })
            current_stitches = end_stitches
    
    # Build result
    result = {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': len(errors) == 0,
        'errors': errors,
        'expanded_rows': expanded_rows,
        'final_stitch_count': current_stitches,
        'bind_off': bind_off
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
