#!/usr/bin/env python3

import sys
import json
import os
import re

def parse_instructions(instruction):
    """Parse a row instruction string into a list of stitch operations."""
    # Split the instruction by commas to get individual operations
    operations = instruction.split(',')
    parsed_ops = []
    
    for op in operations:
        op = op.strip()
        # Match pattern like "k4" or "p3" or "k2tog"
        match = re.match(r'([a-zA-Z]+)(\d*)', op)
        if match:
            stitch_type = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
            # For now, we'll assume all operations maintain the same stitch count
            # A full implementation would need to parse k2tog (decrease) and yo (increase)
            parsed_ops.append({
                "stitch": stitch_type,
                "count": count
            })
    
    return parsed_ops

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    pattern_lines = []
    rows = []
    
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
            rows.append((row_num, instruction))
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
        # For now, we'll just use the cast_on value as the final stitch count
        final_stitch_count = cast_on
        expanded_rows = []
        expanded_row_index = 1
        
        for row_num, instruction in rows:
            # For now, assume start_stitches equals cast_on and no stitch changes
            start_stitches = cast_on
            end_stitches = cast_on  # This will need to be calculated based on instructions
            
            expanded_rows.append({
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
            "expanded_rows": expanded_rows,
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