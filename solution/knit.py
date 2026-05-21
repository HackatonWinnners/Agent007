#!/usr/bin/env python3

import sys
import json
import re

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except IOError:
        print(f"Error: Cannot read file {input_file}", file=sys.stderr)
        sys.exit(2)
    
    # Parse the content
    lines = content.strip().split('\n')
    
    # Initialize output structure
    result = {
        "pattern_name": None,
        "cast_on": None,
        "valid": True,
        "errors": [],
        "expanded_rows": [],
        "final_stitch_count": None,
        "bind_off": False
    }
    
    # Process each line
    line_num = 0
    for line in lines:
        line_num += 1
        stripped_line = line.strip()
        
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('#'):
            continue
            
        # Check for pattern declaration
        if stripped_line.startswith('pattern '):
            pattern_match = re.match(r'pattern\s+"([^"]*)"', stripped_line)
            if pattern_match:
                result["pattern_name"] = pattern_match.group(1)
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_PATTERN",
                    "message": "Malformed pattern declaration",
                    "line": line_num,
                    "row": None
                })
                result["valid"] = False
            continue
            
        # Check for cast_on
        if stripped_line.startswith('cast_on '):
            cast_on_match = re.match(r'cast_on\s+(\d+)', stripped_line)
            if cast_on_match and int(cast_on_match.group(1)) > 0:
                if result["cast_on"] is None:
                    result["cast_on"] = int(cast_on_match.group(1))
                else:
                    result["errors"].append({
                        "type": "error",
                        "code": "DUPLICATE_CAST_ON",
                        "message": "Duplicate cast_on declaration",
                        "line": line_num,
                        "row": None
                    })
                    result["valid"] = False
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_CAST_ON",
                    "message": "Malformed cast_on declaration",
                    "line": line_num,
                    "row": None
                })
                result["valid"] = False
            continue
            
        # Check for row declaration
        if stripped_line.startswith('row '):
            row_match = re.match(r'row\s+(\d+):\s*(.+)', stripped_line)
            if row_match:
                row_num = int(row_match.group(1))
                instruction_list = row_match.group(2)
                
                # Validate row number
                if row_num <= 0:
                    result["errors"].append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "message": "Malformed row declaration",
                        "line": line_num,
                        "row": row_num
                    })
                    result["valid"] = False
                    continue
                    
                # Parse instruction list
                instructions = []
                try:
                    instruction_parts = instruction_list.split(',')
                    for part in instruction_parts:
                        part = part.strip()
                        if part.startswith('['):
                            # Handle bracketed repeats
                            bracket_match = re.match(r'\[(.*)\]\s+x(\d+)', part)
                            if bracket_match:
                                inner_instructions = bracket_match.group(1)
                                count = int(bracket_match.group(2))
                                # Add repeated instructions
                                for _ in range(count):
                                    instructions.extend(parse_instruction_list(inner_instructions))
                            else:
                                result["errors"].append({
                                    "type": "error",
                                    "code": "MALFORMED_ROW",
                                    "message": "Malformed row instruction",
                                    "line": line_num,
                                    "row": row_num
                                })
                                result["valid"] = False
                        else:
                            instructions.append(parse_instruction(part))
                except:
                    result["errors"].append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "message": "Malformed row instruction",
                        "line": line_num,
                        "row": row_num
                    })
                    result["valid"] = False
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Malformed row declaration",
                    "line": line_num,
                    "row": None
                })
                result["valid"] = False
            continue
            
        # Check for bind_off
        if stripped_line == 'bind_off':
            result["bind_off"] = True
            continue
            
        # Check for repeat
        if stripped_line.startswith('repeat '):
            repeat_match = re.match(r'repeat\s+rows\s+(\d+)-(\d+)\s+x(\d+)', stripped_line)
            if repeat_match:
                start_row = int(repeat_match.group(1))
                end_row = int(repeat_match.group(2))
                count = int(repeat_match.group(3))
                
                if start_row <= 0 or end_row <= 0 or count <= 0:
                    result["errors"].append({
                        "type": "error",
                        "code": "INVALID_REPEAT_RANGE",
                        "message": "Invalid repeat range",
                        "line": line_num,
                        "row": None
                    })
                    result["valid"] = False
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_REPEAT",
                    "message": "Malformed repeat declaration",
                    "line": line_num,
                    "row": None
                })
                result["valid"] = False
            continue
    
    # Output the result
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)

def parse_instruction(instruction_str):
    # Parse an instruction string and return a dictionary
    match = re.match(r'([a-z0-9]+)(\d*)', instruction_str)
    if match:
        stitch = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        return {"stitch": stitch, "count": count}
    else:
        return None

def parse_instruction_list(instruction_list_str):
    # Parse an instruction list and return a list of instructions
    instructions = []
    parts = instruction_list_str.split(',')
    for part in parts:
        instruction = parse_instruction(part.strip())
        if instruction:
            instructions.append(instruction)
    return instructions

if __name__ == "__main__":
    main()