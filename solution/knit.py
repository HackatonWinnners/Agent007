#!/usr/bin/env python3

import sys
import json
import os
import re

class KnittingCompiler:
    def __init__(self):
        self.pattern_name = None
        self.cast_on = None
        self.bind_off = False
        self.rows = []
        self.repeats = []
        self.errors = []
        self.line_map = {}  # Map from row number to line number
        
    def parse_file(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                if line.startswith('pattern "'):
                    if self.pattern_name is not None:
                        self.errors.append({
                            "type": "validation",
                            "code": "E_DUPLICATE_PATTERN",
                            "message": "Duplicate pattern name declaration",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    # Extract pattern name
                    match = re.match(r'pattern "(.*)"', line)
                    if not match:
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_BAD_NAME",
                            "message": "Invalid pattern name syntax",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    self.pattern_name = match.group(1)
                
                elif line.startswith('cast_on '):
                    if self.cast_on is not None:
                        self.errors.append({
                            "type": "validation",
                            "code": "E_DUPLICATE_CAST_ON",
                            "message": "Duplicate cast_on declaration",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    try:
                        self.cast_on = int(line.split(' ')[1])
                    except (ValueError, IndexError):
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_BAD_NUMBER",
                            "message": "Invalid cast_on number",
                            "line": i,
                            "row": None
                        })
                        continue
                
                elif line.startswith('bind_off'):
                    if self.bind_off:
                        self.errors.append({
                            "type": "validation",
                            "code": "E_TRAILING_AFTER_BIND_OFF",
                            "message": "bind_off declared twice",
                            "line": i,
                            "row": None
                        })
                        continue
                    self.bind_off = True
                
                elif line.startswith('row '):
                    # Parse row instruction
                    parts = line.split(': ', 1)
                    if len(parts) != 2:
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_UNKNOWN_COMMAND",
                            "message": "Invalid row syntax",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    try:
                        row_number = int(parts[0].split(' ')[1])
                        self.line_map[row_number] = i  # Map row number to line number
                    except (ValueError, IndexError):
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_BAD_NUMBER",
                            "message": "Invalid row number",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    instruction = parts[1]
                    self.rows.append((row_number, instruction))
                
                elif line.startswith('repeat rows '):
                    # Parse repeat instruction
                    parts = line.split(' ')
                    if len(parts) < 4:
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_UNKNOWN_COMMAND",
                            "message": "Invalid repeat syntax",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    repeat_def = parts[2]
                    try:
                        repeat_count = int(parts[3][1:])  # Remove 'x' prefix
                    except (ValueError, IndexError):
                        self.errors.append({
                            "type": "syntax",
                            "code": "E_REPEAT_BAD_COUNT",
                            "message": "Invalid repeat count",
                            "line": i,
                            "row": None
                        })
                        continue
                    
                    if '-' in repeat_def:
                        try:
                            start_row, end_row = map(int, repeat_def.split('-'))
                        except ValueError:
                            self.errors.append({
                                "type": "syntax",
                                "code": "E_REPEAT_BAD_RANGE",
                                "message": "Invalid repeat range",
                                "line": i,
                                "row": None
                            })
                            continue
                    else:
                        try:
                            start_row = end_row = int(repeat_def)
                        except ValueError:
                            self.errors.append({
                                "type": "syntax",
                                "code": "E_REPEAT_BAD_RANGE",
                                "message": "Invalid repeat range",
                                "line": i,
                                "row": None
                            })
                            continue
                    
                    self.repeats.append({
                        "start_row": start_row,
                        "end_row": end_row,
                        "count": repeat_count
                    })
                
                else:
                    # Unknown command
                    self.errors.append({
                        "type": "syntax",
                        "code": "E_UNKNOWN_COMMAND",
                        "message": "Unknown command",
                        "line": i,
                        "row": None
                    })
            except Exception as e:
                self.errors.append({
                    "type": "syntax",
                    "code": "PARSE_ERROR",
                    "message": f"Error parsing line {i}: {str(e)}",
                    "line": i,
                    "row": None
                })
    
    def expand_brackets(self, instruction):
        """Expand bracketed repeats in instruction"""
        # Handle nested brackets by repeatedly expanding until no more brackets
        expanded = instruction
        while True:
            # Find the innermost bracket pattern
            bracket_pattern = r'\[([^\[\]]+)\] x(\d+)'
            match = re.search(bracket_pattern, expanded)
            if not match:
                break
            
            bracket_content = match.group(1)
            repeat_count = int(match.group(2))
            
            # Split bracket content by commas
            operations = [op.strip() for op in bracket_content.split(',')]
            
            # Create repeated content
            repeated_content = ','.join(operations * repeat_count)
            
            # Replace in expanded string
            expanded = expanded[:match.start()] + repeated_content + expanded[match.end():]
        
        return expanded
    
    def parse_instruction(self, instruction):
        """Parse instruction into stitch operations"""
        # First expand brackets
        expanded_instruction = self.expand_brackets(instruction)
        
        # Split by commas
        operations = [op.strip() for op in expanded_instruction.split(',')]
        parsed_ops = []
        
        for op in operations:
            if not op:
                continue
            
            # Match stitch type and count
            match = re.match(r'([a-zA-Z]+)(\d*)', op)
            if not match:
                self.errors.append({
                    "type": "syntax",
                    "code": "E_UNKNOWN_STITCH",
                    "message": f"Invalid stitch syntax: {op}",
                    "line": None,
                    "row": None
                })
                continue
            
            stitch_type = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
            
            parsed_ops.append({
                "stitch": stitch_type,
                "count": count
            })
        
        return parsed_ops
    
    def simulate_row(self, instruction, start_stitches, row_num):
        """Simulate a row and return the end stitch count"""
        parsed_ops = self.parse_instruction(instruction)
        
        # Define stitch behavior
        stitch_behavior = {
            'k': {'consumes': 1, 'produces': 1},
            'p': {'consumes': 1, 'produces': 1},
            'yo': {'consumes': 0, 'produces': 1},
            'k2tog': {'consumes': 2, 'produces': 1},
            'p2tog': {'consumes': 2, 'produces': 1},
            'ssk': {'consumes': 2, 'produces': 1},
            'kfb': {'consumes': 1, 'produces': 2},
            'pfb': {'consumes': 1, 'produces': 2},
            'm1': {'consumes': 0, 'produces': 1},
            'sl': {'consumes': 1, 'produces': 1},
            's': {'consumes': 1, 'produces': 1}
        }
        
        # Track consumed and produced stitches
        total_consumed = 0
        total_produced = 0
        
        for op in parsed_ops:
            stitch_type = op["stitch"]
            count = op["count"]
            
            if stitch_type not in stitch_behavior:
                self.errors.append({
                    "type": "syntax",
                    "code": "E_UNKNOWN_STITCH",
                    "message": f"Unknown stitch type: {stitch_type}",
                    "line": self.line_map.get(row_num, None),
                    "row": row_num
                })
                continue
            
            behavior = stitch_behavior[stitch_type]
            total_consumed += behavior['consumes'] * count
            total_produced += behavior['produces'] * count
        
        # Check for stitch count errors
        if total_consumed > start_stitches:
            self.errors.append({
                "type": "stitch_count",
                "code": "E_STITCH_OVERFLOW",
                "message": f"Stitch overflow: consumed {total_consumed} stitches but only {start_stitches} available",
                "line": self.line_map.get(row_num, None),
                "row": row_num
            })
            return start_stitches  # Return original count on overflow
        
        if total_consumed < start_stitches:
            self.errors.append({
                "type": "stitch_count",
                "code": "E_STITCH_UNDERFLOW",
                "message": f"Stitch underflow: consumed {total_consumed} stitches but needed {start_stitches}",
                "line": self.line_map.get(row_num, None),
                "row": row_num
            })
            return start_stitches  # Return original count on underflow
        
        # Calculate final stitch count
        end_stitches = start_stitches - total_consumed + total_produced
        return end_stitches
    
    def expand_rows(self):
        """Expand rows with repeats"""
        # Create a list of all rows to process
        all_rows = self.rows.copy()
        
        # Handle repeats
        for repeat in self.repeats:
            start_row = repeat["start_row"]
            end_row = repeat["end_row"]
            count = repeat["count"]
            
            # Find rows to repeat
            rows_to_repeat = []
            for row_num, instruction in self.rows:
                if start_row <= row_num <= end_row:
                    rows_to_repeat.append((row_num, instruction))
            
            # Add repeated rows
            for _ in range(count):
                for row_num, instruction in rows_to_repeat:
                    all_rows.append((row_num, instruction))
        
        return all_rows
    
    def compile(self, file_path):
        # Parse the file
        self.parse_file(file_path)
        
        # Check for required fields
        if self.pattern_name is None:
            self.errors.append({
                "type": "validation",
                "code": "E_MISSING_PATTERN_NAME",
                "message": "Missing pattern name",
                "line": None,
                "row": None
            })
        
        if self.cast_on is None:
            self.errors.append({
                "type": "validation",
                "code": "E_MISSING_CAST_ON",
                "message": "Missing cast_on value",
                "line": None,
                "row": None
            })
        
        # If there are errors, return early
        if self.errors:
            return self.get_error_result()
        
        # Expand rows
        expanded_rows = self.expand_rows()
        
        # Simulate rows
        current_stitches = self.cast_on
        result_rows = []
        expanded_row_index = 1
        
        for row_num, instruction in expanded_rows:
            start_stitches = current_stitches
            
            # Simulate the row
            end_stitches = self.simulate_row(instruction, start_stitches, row_num)
            
            # Parse instructions for detailed info
            parsed_instructions = self.parse_instruction(instruction)
            
            result_rows.append({
                "source_row": row_num,
                "expanded_row_index": expanded_row_index,
                "start_stitches": start_stitches,
                "end_stitches": end_stitches,
                "instructions": parsed_instructions
            })
            
            current_stitches = end_stitches
            expanded_row_index += 1
        
        final_stitch_count = current_stitches
        
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": True,
            "errors": [],
            "expanded_rows": result_rows,
            "final_stitch_count": final_stitch_count,
            "bind_off": self.bind_off
        }
    
    def get_error_result(self):
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": False,
            "errors": self.errors,
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": self.bind_off
        }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "compile":
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnittingCompiler()
    result = compiler.compile(input_file)
    
    print(json.dumps(result, indent=2))
    
    if not result["valid"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()