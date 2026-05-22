#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle special operations
    if op == 'dec':
        return {'stitch': 'k2tog', 'count': 1}
    
    # Handle counted stitches like k10, p5, etc.
    match = re.match(r'^([a-z]+)(\d+)$', op)
    if match:
        stitch_type = match.group(1)
        count = int(match.group(2))
        return {'stitch': stitch_type, 'count': count}
    
    # Handle single stitches like yo, k2tog, ssk, inc
    if op in ['yo', 'k2tog', 'ssk', 'inc']:
        return {'stitch': op, 'count': 1}
    
    return None

def expand_bracketed_repeat(instruction_list):
    """Expand bracketed repeats like [k2, p2] x3 into k2, p2, k2, p2, k2, p2"""
    result = []
    i = 0
    while i < len(instruction_list):
        item = instruction_list[i]
        
        # Check if this is a bracketed repeat
        if isinstance(item, str) and item.startswith('['):
            # Find the matching closing bracket
            bracket_count = 1
            j = i + 1
            while j < len(instruction_list) and bracket_count > 0:
                if instruction_list[j].startswith('['):
                    bracket_count += 1
                elif instruction_list[j].endswith(']'):
                    bracket_count -= 1
                j += 1
            
            if bracket_count == 0:
                # Extract the bracketed content
                bracket_content = instruction_list[i+1:j-1]
                
                # Find the repeat count
                repeat_str = instruction_list[j] if j < len(instruction_list) else ''
                match = re.match(r'^x(\d+)$', repeat_str)
                if match:
                    repeat_count = int(match.group(1))
                    # Expand the bracketed content
                    for _ in range(repeat_count):
                        result.extend(bracket_content)
                    i = j  # Skip the processed items
                else:
                    # Invalid repeat syntax
                    result.append(item)
            else:
                result.append(item)
        else:
            result.append(item)
        i += 1
    
    return result

def parse_row(row_line):
    """Parse a row line like 'row 1: k10'"""
    match = re.match(r'^row\s+(\d+)\s*:\s*(.*)$', row_line)
    if not match:
        return None
    
    row_num = int(match.group(1))
    instructions = match.group(2)
    
    # Split by comma and clean up
    parts = [part.strip() for part in instructions.split(',') if part.strip()]
    
    # Expand bracketed repeats
    expanded_parts = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part.startswith('[') and part.endswith(']'):
            # Extract content inside brackets
            inner_content = part[1:-1]
            # Check for repeat syntax
            repeat_match = re.search(r'\s+x(\d+)$', inner_content)
            if repeat_match:
                repeat_count = int(repeat_match.group(1))
                # Extract the instruction list without the repeat part
                instr_list = inner_content[:repeat_match.start()].strip()
                # Split the instruction list
                instr_parts = [p.strip() for p in instr_list.split(',') if p.strip()]
                # Repeat the instructions
                for _ in range(repeat_count):
                    expanded_parts.extend(instr_parts)
                i += 1
                continue
        expanded_parts.append(part)
        i += 1
    
    return {
        'row_num': row_num,
        'instructions': expanded_parts
    }

def simulate_stitch_count(instructions, start_stitches):
    """Simulate stitch count changes for a row"""
    current_stitches = start_stitches
    
    for instr in instructions:
        parsed = parse_stitch_operation(instr)
        if parsed:
            # For simplicity, we'll just count the stitches
            # In a real implementation, this would be more complex
            if parsed['stitch'] in ['k', 'p', 'yo', 'ssk', 'inc']:
                current_stitches += parsed['count']
            elif parsed['stitch'] in ['k2tog', 'dec']:
                current_stitches -= 1
        
    return current_stitches

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
            
            rows.append({
                'row_num': row_num,
                'instructions': instr_parts
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
    
    # Process each row and expand brackets
    for i, row in enumerate(rows):
        # Expand brackets in the row
        expanded_instructions = expand_bracketed_repeat(row['instructions'])
        
        # Add to expanded rows
        expanded_rows.append({
            'expanded_row_index': i + 1,
            'source_row': row['row_num'],
            'instructions': expanded_instructions,
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
            parsed = parse_stitch_operation(instr)
            if parsed:
                if parsed['stitch'] in ['k', 'p', 'yo', 'ssk', 'inc']:
                    end_stitches += parsed['count']
                elif parsed['stitch'] in ['k2tog', 'dec']:
                    end_stitches -= 1
        
        expanded_rows[i]['start_stitches'] = current_stitches
        expanded_rows[i]['end_stitches'] = end_stitches
        
        # Parse instructions for detailed info
        detailed_instructions = []
        for instr in row['instructions']:
            parsed = parse_stitch_operation(instr)
            if parsed:
                detailed_instructions.append(parsed)
            else:
                errors.append({
                    'type': 'error',
                    'code': 'UNKNOWN_STITCH',
                    'message': f'Unknown stitch {instr}.',
                    'line': line_num,
                    'row': row['source_row']
                })
        
        expanded_rows[i]['instructions'] = detailed_instructions
    
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
