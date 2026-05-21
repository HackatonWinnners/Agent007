#!/usr/bin/env python3

import sys
import json
import os
import re

def parse_instructions(instruction):
    """Parse a row instruction string into a list of stitch operations."""
    # Handle bracket notation with nested brackets
    # Keep expanding until no more brackets are found
    while '[' in instruction and ']' in instruction:
        # Find the innermost bracketed sections and their repeat counts
        bracket_pattern = r'\[([^\[\]]+)\]\s*x(\d+)'
        match = re.search(bracket_pattern, instruction)
        if not match:
            break
        
        # Get the full match and groups
        full_match = match.group(0)
        section = match.group(1)
        count_str = match.group(2)
        
        try:
            count = int(count_str)
            # Expand the section
            expanded_section = (section + ', ') * count
            # Remove trailing comma and space
            expanded_section = expanded_section.rstrip(', ')
            # Replace the bracketed section
            instruction = instruction.replace(full_match, expanded_section, 1)
        except ValueError:
            # If count is not a valid integer, return malformed row error
            raise ValueError("Malformed row: invalid repeat count")
    
    # Split the instruction by commas to get individual operations
    operations = instruction.split(',')
    parsed_ops = []
    
    for op in operations:
        op = op.strip()
        if not op:
            continue
        # Match pattern like "k4" or "p3" or "k2tog" or "yo" or "inc"
        match = re.match(r'([a-zA-Z]+)(\d*)', op)
        if match:
            stitch_type = match.group(1)
            count_str = match.group(2)
            count = int(count_str) if count_str else 1
            
            # Handle special cases for stitch count changes
            # For example, k2tog decreases by 1 stitch per occurrence
            # yo and inc increase by 1 stitch per occurrence
            parsed_ops.append({
                "stitch": stitch_type,
                "count": count
            })
    
    return parsed_ops

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    pattern_name = None
    cast_on = None
    bind_off = False
    rows = []
    repeats = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on '):
            cast_on = int(line.split(' ')[1])
        elif line.startswith('bind_off'):
            bind_off = True
        elif line.startswith('row '):
            # Extract row number and instructions
            parts = line.split(': ')
            row_number = int(parts[0].split(' ')[1].rstrip(':'))
            instruction = parts[1] if len(parts) > 1 else ""
            rows.append((row_number, instruction))
        elif line.startswith('repeat rows '):
            # Handle repeat rows instruction
            # Format: repeat rows ROWS xN
            # Example: repeat rows 01-03 x2
            parts = line.split(' ')
            repeat_def = parts[2]  # e.g., "01-03"
            repeat_count = int(parts[3][1:])  # e.g., "2" from "x2"
            # Parse the repeat definition
            if '-' in repeat_def:
                start_row, end_row = repeat_def.split('-')
                start_row = int(start_row)
                end_row = int(end_row)
            else:
                start_row = end_row = int(repeat_def)
            
            repeats.append({
                "start_row": start_row,
                "end_row": end_row,
                "count": repeat_count
            })
    
    return pattern_name, cast_on, bind_off, rows, repeats

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "compile":
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found", file=sys.stderr)
        sys.exit(2)
    
    try:
        pattern_name, cast_on, bind_off, rows, repeats = parse_knit_file(input_file)
        
        # Process the rows to get final stitch count
        current_stitches = cast_on
        expanded_rows = []
        expanded_instructions = []
        expanded_row_index = 1
        
        # First, expand the rows with repeats
        expanded_rows_list = []
        
        # Add the original rows first
        for row_num, instruction in rows:
            expanded_rows_list.append((row_num, instruction))
        
        # Then handle repeats
        for repeat in repeats:
            start_row = repeat["start_row"]
            end_row = repeat["end_row"]
            count = repeat["count"]
            
            # Find the rows to repeat
            rows_to_repeat = []
            for row_num, instruction in rows:
                if start_row <= row_num <= end_row:
                    rows_to_repeat.append((row_num, instruction))
            
            # Add repeated rows
            for _ in range(count):
                for row_num, instruction in rows_to_repeat:
                    expanded_rows_list.append((row_num, instruction))
        
        # Process the expanded rows
        for row_num, instruction in expanded_rows_list:
            start_stitches = current_stitches
            
            # Parse the instruction string into a list of stitch operations
            parsed_instructions = parse_instructions(instruction)
            
            # Calculate stitch count changes based on instructions
            stitch_count = start_stitches
            for op in parsed_instructions:
                stitch_type = op["stitch"]
                count = op["count"]
                if stitch_type == "k2tog":
                    # k2tog decreases stitch count by 1 for each occurrence
                    stitch_count -= count
                elif stitch_type in ["yo", "inc"]:
                    # yo and inc increase stitch count by 1 for each occurrence
                    stitch_count += count
                # Other stitch types like "k" or "p" don't change stitch count
            
            # Update current stitches for next row
            current_stitches = stitch_count
            
            end_stitches = current_stitches
            
            expanded_instructions.append({
                "source_row": row_num,
                "expanded_row_index": expanded_row_index,
                "start_stitches": start_stitches,
                "end_stitches": end_stitches,
                "instructions": parsed_instructions
            })
            expanded_row_index += 1
        
        final_stitch_count = current_stitches
        
        result = {
            "pattern_name": pattern_name,
            "cast_on": cast_on,
            "valid": True,
            "errors": [],
            "expanded_rows": expanded_instructions,
            "final_stitch_count": final_stitch_count,
            "bind_off": bind_off
        }
        
        print(json.dumps(result, indent=2))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "pattern_name": None,
            "cast_on": None,
            "valid": False,
            "errors": [
                {
                    "type": "error",
                    "code": "UNKNOWN_ERROR",
                    "message": str(e),
                    "line": None,
                    "row": None
                }
            ],
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()