#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle counted stitches like k10, p
    match = re.match(r'^(k|p|yo|k2tog|ssk|inc|dec|rep|bind_off|cast_on)(\d*)$', op)
    if not match:
        return None
    
    op_type = match.group(1)
    count = int(match.group(2)) if match.group(2) else 1
    
    return {
        'type': op_type,
        'count': count
    }

def expand_brackets(row_parts):
    """Expand bracketed patterns like [k1, p1] x2"""
    # Find bracketed sections
    result = []
    i = 0
    while i < len(row_parts):
        part = row_parts[i]
        if part.startswith('[') and part.endswith(']'):
            # Extract content between brackets
            content = part[1:-1]
            # Split by comma to get individual operations
            operations = [op.strip() for op in content.split(',')]
            # Check if there's a repeat count
            if i + 1 < len(row_parts) and 'x' in row_parts[i + 1]:
                repeat_count = int(row_parts[i + 1].split('x')[1])
                # Expand the bracketed content
                for _ in range(repeat_count):
                    result.extend(operations)
                i += 2  # Skip both bracketed part and repeat part
            else:
                result.extend(operations)
                i += 1
        else:
            result.append(part)
            i += 1
    return result

def simulate_row(row_instructions, start_stitches):
    """Simulate a row and return the stitch count"""
    current_stitches = start_stitches
    
    for instruction in row_instructions:
        if instruction['type'] == 'k' or instruction['type'] == 'p':
            # These operations don't change stitch count
            pass
        elif instruction['type'] == 'k2tog':
            # This reduces stitch count by 1
            if current_stitches >= 2:
                current_stitches -= 1
            else:
                raise ValueError(f"Not enough stitches for k2tog: {current_stitches}")
        elif instruction['type'] == 'inc':
            # This increases stitch count by 1
            current_stitches += 1
        elif instruction['type'] == 'yo':
            # This increases stitch count by 1
            current_stitches += 1
        elif instruction['type'] == 'ssk':
            # This reduces stitch count by 1
            if current_stitches >= 2:
                current_stitches -= 1
            else:
                raise ValueError(f"Not enough stitches for ssk: {current_stitches}")
        elif instruction['type'] == 'dec':
            # This reduces stitch count by 1
            if current_stitches >= 2:
                current_stitches -= 1
            else:
                raise ValueError(f"Not enough stitches for dec: {current_stitches}")
    
    return current_stitches

def parse_row(row_line):
    """Parse a row line like 'row 1: k10'"""
    # Remove comments
    row_line = row_line.split('#')[0].strip()
    
    # Extract row number and instructions
    match = re.match(r'^row\s+(\d+):\s*(.*)$', row_line)
    if not match:
        return None
    
    row_num = int(match.group(1))
    instructions = match.group(2)
    
    # Split instructions by comma
    parts = [part.strip() for part in instructions.split(',')]
    
    # Expand brackets
    expanded_parts = expand_brackets(parts)
    
    # Parse each instruction
    parsed_instructions = []
    for part in expanded_parts:
        parsed = parse_stitch_operation(part)
        if parsed:
            parsed_instructions.append(parsed)
        else:
            # If it's not a valid stitch operation, it might be a repeat
            if part.startswith('[') and part.endswith(']'):
                # This is a bracketed pattern
                pass
            else:
                return None
    
    return {
        'row': row_num,
        'instructions': parsed_instructions
    }

def main():
    if len(sys.argv) < 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(json.dumps({
            'pattern_name': '',
            'cast_on': 0,
            'valid': False,
            'errors': [{'type': 'error', 'code': 'FILE_NOT_FOUND', 'message': f"File not found: {input_file}", 'line': 0}]
        }), file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Unknown Pattern"
    cast_on = 0
    bind_off = False
    rows = []
    errors = []
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line:
            continue
        
        # Parse pattern name
        pattern_match = re.match(r'^pattern\s+"(.*)"$', line)
        if pattern_match:
            pattern_name = pattern_match.group(1)
            continue
        
        # Parse cast_on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            cast_on = int(cast_on_match.group(1))
            continue
        
        # Parse bind_off
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            bind_off = True
            continue
        
        # Parse rows
        row_match = re.match(r'^row\s+(\d+):\s*(.*)$', line)
        if row_match:
            row_result = parse_row(line)
            if row_result:
                rows.append(row_result)
            else:
                errors.append({
                    'type': 'error',
                    'code': 'INVALID_ROW',
                    'message': f"Invalid row syntax: {line}",
                    'line': i + 1
                })
            continue
        
        # If we get here, it's an unrecognized line
        errors.append({
            'type': 'error',
            'code': 'UNRECOGNIZED_LINE',
            'message': f"Unrecognized line: {line}",
            'line': i + 1
        })
    
    # Validate that we have a pattern name and cast_on
    if not pattern_name or cast_on == 0:
        errors.append({
            'type': 'error',
            'code': 'MISSING_REQUIRED_FIELDS',
            'message': "Pattern must have a name and cast_on value",
            'line': 0
        })
    
    # Simulate rows
    expanded_rows = []
    current_stitches = cast_on
    
    for row in rows:
        try:
            # Simulate the row
            end_stitches = simulate_row(row['instructions'], current_stitches)
            
            expanded_rows.append({
                'row': row['row'],
                'start_stitches': current_stitches,
                'instructions': row['instructions'],
                'end_stitches': end_stitches
            })
            
            current_stitches = end_stitches
        except Exception as e:
            errors.append({
                'type': 'error',
                'code': 'ROW_SIMULATION_ERROR',
                'message': str(e),
                'line': 0
            })
    
    # Build result
    result = {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': len(errors) == 0,
        'errors': errors,
        'expanded_rows': expanded_rows,
        'final_stitch_count': current_stitches if expanded_rows else cast_on,
        'bind_off': bind_off
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
