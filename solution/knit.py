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
    
    # Simulate stitch counts
    current_stitches = cast_on
    for i, row in enumerate(rows):
        # Calculate end stitches
        end_stitches = current_stitches
        
        for instr in row['instructions']:
            parsed = parse_stitch_operation(instr)
            if parsed:
                # For each stitch type, calculate the net change
                if parsed['stitch'] in ['k', 'p', 'yo', 'ssk', 'inc']:
                    # These consume and produce the same number of stitches
                    end_stitches += parsed['count']
                elif parsed['stitch'] in ['k2tog', 'dec']:
                    # These consume 2 stitches and produce 1 stitch (net -1)
                    end_stitches -= 1
            else:
                errors.append({
                    'type': 'error',
                    'code': 'UNKNOWN_STITCH',
                    'message': f'Unknown stitch {instr}.',
                    'line': line_num,
                    'row': row['row_num']
                })
        
        # Add to expanded rows
        expanded_rows.append({
            'expanded_row_index': i + 1,
            'source_row': row['row_num'],
            'instructions': row['instructions'],
            'start_stitches': current_stitches,
            'end_stitches': end_stitches
        })
        
        current_stitches = end_stitches
    
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
