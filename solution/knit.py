#!/usr/bin/env python3

import sys
import json
import os
import re


def parse_stitch_operation(op):
    """Parse a stitch operation like 'k1', 'p2', 'k2tog', etc."""
    # Remove comments and whitespace
    op = op.split('#')[0].strip()
    
    # Handle special operations like k2tog, yo, inc, dec
    if op in ['k2tog', 'ssk', 'inc', 'dec', 'yo']:
        return {'stitch': op, 'count': 1}
    
    # Handle simple stitch operations like k1, p1
    simple_pattern = re.compile(r'^([a-z]+)(\d*)$')
    match = simple_pattern.match(op)
    if match:
        stitch_type = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        return {'stitch': stitch_type, 'count': count}
    
    # If we get here, it's an unknown stitch
    return {'stitch': op, 'count': 1}


def expand_brackets(instruction):
    """Expand bracketed instructions like [k1, p1] x2 into repeated instructions."""
    # Handle bracket syntax: [k1, p1] x2
    # First, let's handle simple brackets
    bracket_pattern = re.compile(r'\[([^\]]+)\] x(\d+)')
    
    # Replace all bracket expressions
    def replace_brackets(match):
        content = match.group(1)
        repeat_count = int(match.group(2))
        # Split the content by comma to get individual operations
        operations = [op.strip() for op in content.split(',') if op.strip()]
        # Repeat the operations
        expanded = []
        for _ in range(repeat_count):
            expanded.extend(operations)
        return ','.join(expanded)
    
    # Handle nested brackets by repeatedly applying the replacement
    result = instruction
    while True:
        new_result = bracket_pattern.sub(replace_brackets, result)
        if new_result == result:
            break
        result = new_result
    
    return result


def simulate_stitch_count(instructions, initial_stitches):
    """Simulate stitch count changes through instructions."""
    current_stitches = initial_stitches
    
    for instruction in instructions:
        op = parse_stitch_operation(instruction)
        stitch_type = op['stitch']
        count = op['count']
        
        # Handle special cases
        if stitch_type == 'dec':
            # dec is an alias for k2tog
            stitch_type = 'k2tog'
        
        if stitch_type in ['k', 'p']:
            # k and p don't change stitch count
            pass
        elif stitch_type == 'k2tog':
            # k2tog decreases stitch count by 1 per occurrence
            # Each k2tog consumes 2 stitches and produces 1 stitch
            if current_stitches < 2:
                return None  # Underflow
            current_stitches -= 1
        elif stitch_type in ['yo', 'inc']:
            # yo and inc increase stitch count by 1 per occurrence
            current_stitches += count
        elif stitch_type == 'ssk':
            # ssk decreases stitch count by 1 per occurrence
            # Each ssk consumes 2 stitches and produces 1 stitch
            if current_stitches < 2:
                return None  # Underflow
            current_stitches -= 1
        
        # Check for overflow
        if current_stitches > 10000:
            return None  # Overflow
    
    return current_stitches


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
    
    pattern_name = "Unknown"
    cast_on = 0
    rows = []
    bind_off = False
    
    for line in lines:
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on '):
            cast_on = int(line.split()[1])
        elif line.startswith('row '):
            # Extract row number and instructions
            parts = line.split(':', 1)
            if len(parts) == 2:
                row_num = int(parts[0].split()[1])
                instructions = parts[1].strip()
                # Expand brackets
                expanded_instructions = expand_brackets(instructions)
                rows.append((row_num, expanded_instructions))
        elif line == 'bind_off':
            bind_off = True
    
    # Validate that we have cast_on and rows
    if cast_on == 0:
        error_result = {
            "pattern_name": pattern_name,
            "cast_on": cast_on,
            "valid": False,
            "errors": ["No cast_on specified"],
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": bind_off
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    
    # Process rows
    expanded_rows = []
    final_stitch_count = cast_on
    
    for row_num, instructions_str in rows:
        # Split instructions by comma
        instructions = [inst.strip() for inst in instructions_str.split(',') if inst.strip()]
        
        # Calculate stitch count for this row
        start_stitches = final_stitch_count
        end_stitches = simulate_stitch_count(instructions, start_stitches)
        
        # If there was an underflow or overflow, we should stop
        if end_stitches is None:
            # For now, let's just skip this row
            continue
        
        # Parse instructions into operation objects
        parsed_instructions = []
        for instruction in instructions:
            op = parse_stitch_operation(instruction)
            parsed_instructions.append(op)
        
        expanded_rows.append({
            "source_row": row_num,
            "expanded_row_index": len(expanded_rows) + 1,
            "start_stitches": start_stitches,
            "end_stitches": end_stitches,
            "instructions": parsed_instructions
        })
        
        final_stitch_count = end_stitches
    
    # Create result
    result = {
        "pattern_name": pattern_name,
        "cast_on": cast_on,
        "valid": True,
        "errors": [],
        "expanded_rows": expanded_rows,
        "final_stitch_count": final_stitch_count,
        "bind_off": bind_off
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
