#!/usr/bin/env python3

import sys
import json
import re

class KnitCompiler:
    def __init__(self):
        self.pattern_name = None
        self.cast_on = None
        self.rows = []
        self.bind_off = False
        self.errors = []
        self.source_rows = {}
        self.expanded_rows = []
        self.final_stitch_count = None
        
    def parse_file(self, file_path):
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Parse lines
        for i, line in enumerate(lines, 1):
            # Remove comments
            if '#' in line:
                line = line.split('#', 1)[0].strip()
            
            if not line:
                continue
            
            # Parse pattern
            if line.startswith('pattern "'):
                if self.pattern_name is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_PATTERN",
                        "message": "Duplicate pattern declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        self.pattern_name = line.split('pattern "', 1)[1].rsplit('"', 1)[0]
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_PATTERN",
                            "message": "Malformed pattern declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse cast_on
            elif line.startswith('cast_on '):
                if self.cast_on is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_CAST_ON",
                        "message": "Duplicate cast_on declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        value = int(line.split('cast_on ')[1])
                        if value <= 0:
                            raise ValueError()
                        self.cast_on = value
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_CAST_ON",
                            "message": "Malformed cast_on declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse row
            elif line.startswith('row '):
                # Check if this is a valid row line
                if ':' not in line:
                    self.errors.append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "message": "Malformed row declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        row_part, content = line.split(':', 1)
                        row_num = int(row_part.split()[1])
                        self.source_rows[row_num] = content.strip()
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_ROW",
                            "message": "Malformed row declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse bind_off
            elif line == 'bind_off':
                if self.bind_off:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_BIND_OFF",
                        "message": "Duplicate bind_off declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    self.bind_off = True
            
            # Unknown statement
            else:
                self.errors.append({
                    "type": "error",
                    "code": "UNKNOWN_STATEMENT",
                    "message": "Unknown statement.",
                    "line": i,
                    "row": None
                })
        
        # Validate required fields
        if self.pattern_name is None:
            self.errors.append({
                "type": "error",
                "code": "MISSING_PATTERN",
                "message": "Missing pattern declaration.",
                "line": None,
                "row": None
            })
        
        if self.cast_on is None:
            self.errors.append({
                "type": "error",
                "code": "MISSING_CAST_ON",
                "message": "Missing cast_on declaration.",
                "line": None,
                "row": None
            })
        
        # Process rows
        self.expand_rows()
        
        # Calculate final stitch count
        if self.cast_on is not None and self.expanded_rows:
            self.final_stitch_count = self.expanded_rows[-1]["end_stitches"]
        elif self.cast_on is not None:
            self.final_stitch_count = self.cast_on
        
        return self.get_result()
    
    def parse_instructions(self, content):
        """Parse instruction content into a list of instruction objects"""
        instructions = []
        # Split by space to get individual instructions
        parts = content.split()
        
        for part in parts:
            # Handle repeat syntax like "2x k2"
            if 'x' in part and part.count('x') == 1:
                # Split on 'x' to get repeat count and instruction
                repeat_count, instruction = part.split('x', 1)
                try:
                    repeat_count = int(repeat_count)
                    # For now, just add the instruction once
                    # In the future we'll expand repeats
                    instructions.append({
                        "type": "instruction",
                        "content": instruction,
                        "repeat": repeat_count
                    })
                except ValueError:
                    # Invalid repeat count
                    instructions.append({
                        "type": "error",
                        "message": f"Invalid repeat count: {repeat_count}",
                        "content": part
                    })
            else:
                # Regular instruction
                instructions.append({
                    "type": "instruction",
                    "content": part
                })
        
        return instructions
    
    def expand_rows(self):
        # Process rows in order
        for row_num in sorted(self.source_rows.keys()):
            content = self.source_rows[row_num]
            instructions = self.parse_instructions(content)
            
            # Calculate stitch count
            start_stitches = self.cast_on if len(self.expanded_rows) == 0 else self.expanded_rows[-1]["end_stitches"]
            
            # For now, just add the row with instructions
            self.expanded_rows.append({
                "expanded_row_index": len(self.expanded_rows) + 1,
                "source_row": row_num,
                "instructions": instructions,
                "start_stitches": start_stitches,
                "end_stitches": start_stitches
            })
    
    def get_result(self):
        valid = len(self.errors) == 0
        if not valid:
            self.expanded_rows = []
            self.final_stitch_count = None
        
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": valid,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": self.final_stitch_count,
            "bind_off": self.bind_off
        }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        compiler = KnitCompiler()
        result = compiler.parse_file(input_file)
        print(json.dumps(result))
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()