#!/usr/bin/env python3

import sys
import json
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle counted stitches like k10, p
    match = re.match(r'^(k|p|yo|k2tog|ssk|inc|dec|sl|rep|rep2|rep3|rep4|rep5|rep6|rep7|rep8|rep9|rep10)(\d*)$', op)
    if not match:
        return None
    
    operation = match.group(1)
    count = int(match.group(2)) if match.group(2) else 1
    
    return {
        'operation': operation,
        'count': count
    }

def expand_brackets(row_content):
    """Expand bracketed patterns like [k1, p1] x2"""
    # Find bracketed content
    bracket_pattern = r'\[([^\]]+)\] x(\d+)'
    match = re.search(bracket_pattern, row_content)
    
    if not match:
        return row_content
    
    # Extract the content inside brackets and repeat count
    bracket_content = match.group(1)
    repeat_count = int(match.group(2))
    
    # Split the bracket content into individual operations
    operations = [op.strip() for op in bracket_content.split(',')]
    
    # Repeat the operations
    expanded_operations = operations * repeat_count
    
    # Replace the bracketed pattern with expanded operations
    expanded_content = row_content.replace(match.group(0), ','.join(expanded_operations))
    
    return expanded_content

def simulate_row(row_content, current_stitches):
    """Simulate a single row and return the new stitch count"""
    # Parse the row content
    if row_content.startswith('row '):
        # Extract just the instructions part
        instructions_part = row_content.split(':', 1)[1].strip()
    else:
        instructions_part = row_content
    
    # Expand brackets if present
    expanded_content = expand_brackets(instructions_part)
    
    # Split into individual operations
    operations = [op.strip() for op in expanded_content.split(',') if op.strip()]
    
    # Process each operation
    stitch_change = 0
    for op in operations:
        parsed_op = parse_stitch_operation(op)
        if not parsed_op:
            return None, f"Invalid stitch operation: {op}"
        
        operation = parsed_op['operation']
        count = parsed_op['count']
        
        if operation in ['k', 'p']:
            # k and p don't change stitch count
            pass
        elif operation in ['k2tog', 'ssk']:
            # These reduce stitch count by 1
            stitch_change -= 1
        elif operation in ['inc']:
            # These increase stitch count by 1
            stitch_change += 1
        elif operation in ['yo']:
            # These increase stitch count by 1
            stitch_change += 1
        elif operation in ['dec']:
            # This reduces stitch count by 1
            stitch_change -= 1
        elif operation in ['sl']:
            # This doesn't change stitch count
            pass
        
    return current_stitches + stitch_change, None

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
            'pattern_name': 'Unknown',
            'cast_on': 0,
            'valid': False,
            'errors': [{'type': 'error', 'code': 'FILE_NOT_FOUND', 'message': f"File not found: {input_file}", 'line': 0}]
        }), file=sys.stderr)
        sys.exit(1)
    
    # Parse the file
    pattern_name = "Unknown"
    cast_on = 0
    bind_off = False
    rows = []
    
    for i, line in enumerate(lines):
        if line.startswith('pattern '):
            pattern_name = line.split(' ', 1)[1].strip('"')
        elif line.startswith('cast_on '):
            cast_on = int(line.split(' ', 1)[1])
        elif line.startswith('bind_off'):
            bind_off = True
        elif line.startswith('row '):
            rows.append(line)
    
    # Validate required fields
    if cast_on == 0:
        return json.dumps({
            'pattern_name': pattern_name,
            'cast_on': cast_on,
            'valid': False,
            'errors': [{'type': 'error', 'code': 'MISSING_CAST_ON', 'message': 'Missing cast_on instruction', 'line': 0}]
        })
    
    # Process rows
    expanded_rows = []
    current_stitches = cast_on
    
    for i, row in enumerate(rows):
        # Parse row
        if row.startswith('row '):
            # Extract just the instructions part
            instructions_part = row.split(':', 1)[1].strip()
        else:
            instructions_part = row
        
        # Expand brackets if present
        expanded_content = expand_brackets(instructions_part)
        
        # Split into individual operations
        operations = [op.strip() for op in expanded_content.split(',') if op.strip()]
        
        # Process each operation
        stitch_change = 0
        for op in operations:
            parsed_op = parse_stitch_operation(op)
            if not parsed_op:
                return json.dumps({
                    'pattern_name': pattern_name,
                    'cast_on': cast_on,
                    'valid': False,
                    'errors': [{'type': 'error', 'code': 'INVALID_STITCH', 'message': f"Invalid stitch operation: {op}", 'line': i+1, 'row': i+1}]
                })
            
            operation = parsed_op['operation']
            count = parsed_op['count']
            
            if operation in ['k', 'p']:
                # k and p don't change stitch count
                pass
            elif operation in ['k2tog', 'ssk']:
                # These reduce stitch count by 1
                stitch_change -= 1
            elif operation in ['inc']:
                # These increase stitch count by 1
                stitch_change += 1
            elif operation in ['yo']:
                # These increase stitch count by 1
                stitch_change += 1
            elif operation in ['dec']:
                # This reduces stitch count by 1
                stitch_change -= 1
            elif operation in ['sl']:
                # This doesn't change stitch count
                pass
        
        # Calculate new stitch count
        new_stitches = current_stitches + stitch_change
        
        # Add to expanded rows
        expanded_rows.append({
            'row_number': i + 1,
            'instructions': operations,
            'start_stitches': current_stitches,
            'end_stitches': new_stitches
        })
        
        current_stitches = new_stitches
    
    result = {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': True,
        'errors': [],
        'expanded_rows': expanded_rows,
        'final_stitch_count': current_stitches,
        'bind_off': bind_off
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
