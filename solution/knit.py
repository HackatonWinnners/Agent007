#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle counted stitches like k10, p5, etc.
    match = re.match(r'^([a-z]+)(\d+)$', op)
    if match:
        stitch_type = match.group(1)
        count = int(match.group(2))
        return {'stitch': stitch_type, 'count': count}
    
    # Handle single stitches like yo, k2tog, ssk, inc
    if op in ['yo', 'k2tog', 'ssk', 'inc', 'dec']:
        return {'stitch': op, 'count': 1}
    
    # Handle k, p, etc. without count
    if op in ['k', 'p']:
        return {'stitch': op, 'count': 1}
    
    return None

def calculate_stitch_change(stitch_op):
    """Calculate the net change in stitch count for a stitch operation"""
    stitch_type = stitch_op['stitch']
    
    # For k, p - consume 1 stitch, produce 1 stitch (net 0)
    if stitch_type in ['k', 'p']:
        return 0
    
    # For yo, ssk, inc - consume 0 stitches, produce 1 stitch (net +1)
    if stitch_type in ['yo', 'ssk', 'inc']:
        return 1
    
    # For k2tog, dec - consume 2 stitches, produce 1 stitch (net -1)
    if stitch_type in ['k2tog', 'dec']:
        return -1
    
    return 0

def expand_brackets(instructions):
    """Expand bracketed repeats in instructions"""
    expanded = []
    
    for instr in instructions:
        # Check if instruction has brackets
        if instr.startswith('[') and instr.endswith(']'):
            # Extract the pattern and repeat count
            pattern_content = instr[1:-1].strip()
            
            # Find repeat count (x<number>) at the end
            repeat_match = re.search(r'x(\d+)$', pattern_content)
            if repeat_match:
                repeat_count = int(repeat_match.group(1))
                # Remove the repeat part to get just the pattern
                pattern_only = pattern_content[:repeat_match.start()].strip()
                
                # Split the pattern into individual instructions
                pattern_parts = [part.strip() for part in pattern_only.split(',') if part.strip()]
                
                # Add the pattern repeated times
                for _ in range(repeat_count):
                    expanded.extend(pattern_parts)
            else:
                # No repeat count, add as-is
                expanded.append(instr)
        else:
            expanded.append(instr)
    
    return expanded

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = [line.rstrip() for line in f.readlines()]
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Parse the file
    pattern_name = None
    cast_on = None
    rows = []
    bind_off = False
    errors = []
    
    line_num = 0
    for line in lines:
        line_num += 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Pattern declaration
        pattern_match = re.match(r'^pattern\s+"(.*)"$', line)
        if pattern_match:
            if pattern_name is not None:
                errors.append({
                    'type': 'error',
                    'code': 'DUPLICATE_PATTERN',
                    'message': 'Duplicate pattern declaration.',
                    'line': line_num,
                    'row': None
                })
            else:
                pattern_name = pattern_match.group(1)
            continue
        
        # Cast on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            if cast_on is not None:
                errors.append({
                    'type': 'error',
                    'code': 'DUPLICATE_CAST_ON',
                    'message': 'Duplicate cast-on declaration.',
                    'line': line_num,
                    'row': None
                })
            else:
                cast_on = int(cast_on_match.group(1))
            continue
        
        # Row
        row_match = re.match(r'^row\s+(\d+)\s*:\s*(.*)$', line)
        if row_match:
            row_num = int(row_match.group(1))
            instructions = row_match.group(2)
            
            # Split instructions by comma
            instr_parts = [part.strip() for part in instructions.split(',') if part.strip()]
            
            # Check for malformed row (empty instruction list)
            if not instr_parts:
                errors.append({
                    'type': 'error',
                    'code': 'MALFORMED_ROW',
                    'message': 'Row has no instructions.',
                    'line': line_num,
                    'row': row_num
                })
                continue
            
            # Expand brackets
            expanded_parts = expand_brackets(instr_parts)
            
            # Parse each instruction
            parsed_instructions = []
            for instr in expanded_parts:
                parsed = parse_stitch_operation(instr)
                if parsed is None:
                    errors.append({
                        'type': 'error',
                        'code': 'INVALID_STITCH',
                        'message': f'Invalid stitch operation: {instr}',
                        'line': line_num,
                        'row': row_num
                    })
                else:
                    parsed_instructions.append(parsed)
            
            if not errors:  # Only add row if no errors in instructions
                rows.append({
                    'row_num': row_num,
                    'instructions': parsed_instructions
                })
            continue
        
        # Bind off
        if line == 'bind_off':
            bind_off = True
            continue
        
        # Unknown statement
        errors.append({
            'type': 'error',
            'code': 'UNKNOWN_STATEMENT',
            'message': 'Unknown statement.',
            'line': line_num,
            'row': None
        })
    
    # Validate
    if pattern_name is None:
        errors.append({
            'type': 'error',
            'code': 'MISSING_PATTERN',
            'message': 'Missing pattern declaration.',
            'line': None,
            'row': None
        })
    
    if cast_on is None:
        errors.append({
            'type': 'error',
            'code': 'MISSING_CAST_ON',
            'message': 'Missing cast-on declaration.',
            'line': None,
            'row': None
        })
    
    # Check for errors
    if errors:
        result = {
            'pattern_name': pattern_name,
            'cast_on': cast_on,
            'valid': False,
            'errors': errors,
            'expanded_rows': [],
            'final_stitch_count': None,
            'bind_off': bind_off
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Process rows
    expanded_rows = []
    
    # Process each row
    for i, row in enumerate(rows):
        # Add to expanded rows
        expanded_rows.append({
            'expanded_row_index': i + 1,
            'source_row': row['row_num'],
            'instructions': row['instructions'],
            'start_stitches': cast_on if i == 0 else expanded_rows[i-1]['end_stitches'],
            'end_stitches': 0  # Will be calculated
        })
    
    # Simulate stitch counts
    for i, row in enumerate(expanded_rows):
        if i == 0:
            current_stitches = cast_on
        else:
            current_stitches = expanded_rows[i-1]['end_stitches']
        
        # Calculate end stitches
        end_stitches = current_stitches
        for instr in row['instructions']:
            change = calculate_stitch_change(instr)
            end_stitches += change
        
        expanded_rows[i]['start_stitches'] = current_stitches
        expanded_rows[i]['end_stitches'] = end_stitches
    
    # Final result
    result = {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': True,
        'errors': [],
        'expanded_rows': expanded_rows,
        'final_stitch_count': expanded_rows[-1]['end_stitches'] if expanded_rows else cast_on,
        'bind_off': bind_off
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
