#!/usr/bin/env python3

import sys
import json
import os
import re

def parse_instructions(instruction):
    """Parse a row instruction string into a list of stitch operations."""
    # This is a simplified parser that just handles basic k (knit) instructions
    # In a full implementation, this would need to handle more stitch types
    # and operations like k2tog, yo, etc.
    
    # Split the instruction by commas to get individual operations
    operations = instruction.split(',')
    parsed_ops = []
    
    for op in operations:
        op = op.strip()
        # Match pattern like "k4" or "p3" or "k2tog"
        # This is a basic implementation that needs to be expanded
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
        lines = f.readlines()
    
    pattern_name = None
    cast_on = None
    bind_off = False
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
            rows.append((row_number, instruction))
    
    return pattern_name, cast_on, bind_off, rows

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "compile":
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found", file=sys.stderr)
        sys.exit(2)
    
    try:
        pattern_name, cast_on, bind_off, rows = parse_knit_file(input_file)
        
        # Process the rows to get final stitch count
        current_stitches = cast_on
        expanded_rows = []
        expanded_row_index = 1
        
        for row_num, instruction in rows:
            start_stitches = current_stitches
            
            # Parse the instruction string into a list of stitch operations
            parsed_instructions = parse_instructions(instruction)
            
            # Calculate stitch count changes based on instructions
            for op in parsed_instructions:
                stitch_type = op["stitch"]
                count = op["count"]
                if stitch_type == "k2tog":
                    # k2tog decreases stitch count by 1 for each occurrence
                    current_stitches -= count
                elif stitch_type == "yo":
                    # yo increases stitch count by 1 for each occurrence
                    current_stitches += count
                # Other stitch types like "k" or "p" don't change stitch count
            
            end_stitches = current_stitches
            
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