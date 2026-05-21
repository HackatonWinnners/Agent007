#!/usr/bin/env python3

import sys
import json
import os
import re

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
        # For now, we'll just use the cast_on value as the final stitch count
        final_stitch_count = cast_on
        
        # Create expanded_rows list
        expanded_rows = []
        for row_num, instruction in rows:
            expanded_rows.append({
                "source_row": row_num,
                "instructions": instruction
            })
        
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