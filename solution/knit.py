#!/usr/bin/env python3

import sys
import json
import os
import re

def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Handle simple stitch operations like k1, p1
    simple_pattern = re.compile(r'^([a-z]+)(\d*)$')
    match = simple_pattern.match(op.strip())
    if match:
        stitch_type = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        return {'stitch': stitch_type, 'count': count}
    
    # Handle special operations like k2tog, yo, inc
    special_pattern = re.compile(r'^([a-z]+)$')
    match = special_pattern.match(op.strip())
    if match:
        stitch_type = match.group(1)
        return {'stitch': stitch_type, 'count': 1}
    
    return None

def expand_brackets(instruction):
    """Expand bracketed instructions like [k1, p1] x2 into repeated instructions."""
    # Handle bracket syntax: [k1, p1] x2
    bracket_pattern = re.compile(r'\[([^\]]+)\] x(\d+)')
    matches = bracket_pattern.findall(instruction)
    
    if matches:
        # For each match, expand the bracketed content
        expanded = []
        for content, repeat_count in matches:
            # Split the content by comma to get individual operations
            operations = [op.strip() for op in content.split(',')]
            # Repeat the operations
            for _ in range(int(repeat_count)):
                expanded.extend(operations)
        
        # Replace the bracketed part with expanded operations
        result = instruction
        for content, repeat_count in matches:
            bracket_text = f'[{content}] x{repeat_count}'
            result = result.replace(bracket_text, ','.join(expanded), 1)
        
        return result
    
    return instruction

def calculate_stitch_change(op):
    """Calculate the change in stitch count for a given operation."""
    if op['stitch'] in ['k', 'p']:
        return 0  # Knit and purl don't change stitch count
    elif op['stitch'] == 'k2tog':
        return -1  # k2tog decreases stitch count by 1
    elif op['stitch'] in ['yo', 'inc']:
        return 1  # yo and inc increase stitch count by 1
    else:
        return 0  # Default case

def simulate_row(row_instructions, initial_stitches):
    """Simulate a row and return the final stitch count."""
    current_stitches = initial_stitches
    
    # Parse instructions
    instructions = []
    for instruction in row_instructions:
        # Expand brackets first
        expanded = expand_brackets(instruction)
        
        # Split by comma to get individual operations
        ops = [op.strip() for op in expanded.split(',')]
        
        for op in ops:
            if op:
                parsed_op = parse_stitch_operation(op)
                if parsed_op:
                    instructions.append(parsed_op)
    
    # Simulate each instruction
    for instruction in instructions:
        change = calculate_stitch_change(instruction)
        current_stitches += change
        
    return current_stitches, instructions

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        error_result = {
            "pattern_name": "Unknown",
            "cast_on": 0,
            "valid": False,
            "errors": ["File not found: " + input_file],
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    
    # Read and parse the input file
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # Parse the pattern
    pattern_name = "Unknown"
    cast_on = 0
    rows = []
    
    for line in lines:
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on '):
            cast_on = int(line.split()[1])
        elif line.startswith('row '):
            # Extract the row number and instruction
            row_match = re.match(r'row (\d+): (.+)', line)
            if row_match:
                row_num = int(row_match.group(1))
                instruction = row_match.group(2)
                rows.append((row_num, instruction))
            
    # Validate required fields
    if not pattern_name or cast_on == 0:
        error_result = {
            "pattern_name": pattern_name,
            "cast_on": cast_on,
            "valid": False,
            "errors": ["Invalid pattern definition"],
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    
    # Process rows
    expanded_rows = []
    current_stitches = cast_on
    
    for row_num, instruction in rows:
        # Expand brackets
        expanded_instruction = expand_brackets(instruction)
        
        # Parse instructions
        ops = [op.strip() for op in expanded_instruction.split(',')]
        parsed_ops = []
        
        for op in ops:
            if op:
                parsed_op = parse_stitch_operation(op)
                if parsed_op:
                    parsed_ops.append(parsed_op)
                
        # Calculate stitch count
        final_stitches = current_stitches
        for op in parsed_ops:
            change = calculate_stitch_change(op)
            final_stitches += change
        
        # Add to expanded rows
        expanded_rows.append({
            "source_row": row_num,
            "expanded_row_index": len(expanded_rows) + 1,
            "start_stitches": current_stitches,
            "end_stitches": final_stitches,
            "instructions": parsed_ops
        })
        
        current_stitches = final_stitches
    
    # Final stitch count
    final_stitch_count = current_stitches
    
    # Build result
    result = {
        "pattern_name": pattern_name,
        "cast_on": cast_on,
        "valid": True,
        "errors": [],
        "expanded_rows": expanded_rows,
        "final_stitch_count": final_stitch_count,
        "bind_off": False
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
