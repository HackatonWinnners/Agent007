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
        
    def add_error(self, message, line=None, row=None, code=None):
        error = {
            "type": "error",
            "code": code or "UNKNOWN_ERROR",
            "message": message,
            "line": line,
            "row": row
        }
        self.errors.append(error)
        
    def parse_line(self, line, line_num):
        line = line.strip()
        if not line:
            return
        
        if line.startswith("pattern "):
            self.pattern_name = line[8:].strip('"')
        elif line.startswith("cast_on "):
            try:
                self.cast_on = int(line[8:])
            except ValueError:
                self.add_error("Invalid cast_on value", line=line_num)
        elif line.startswith("bind_off"):
            self.bind_off = True
        elif line.startswith("row "):
            # Extract row number and instruction
            row_match = re.match(r"row ([0-9]+):(.*)", line)
            if row_match:
                row_num = int(row_match.group(1))
                instruction = row_match.group(2).strip()
                self.rows.append((row_num, instruction))
            else:
                self.add_error("Invalid row format", line=line_num)
        elif line.startswith("repeat "):
            # Handle repeat blocks
            repeat_match = re.match(r"repeat ([0-9]+) times:(.*)", line)
            if repeat_match:
                times = int(repeat_match.group(1))
                instruction = repeat_match.group(2).strip()
                self.repeats.append((times, instruction))
            else:
                self.add_error("Invalid repeat format", line=line_num)
        
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
            
            # Extract content and repeat count
            content = match.group(1)
            repeat_count = int(match.group(2))
            
            # Split content by comma and repeat
            operations = [op.strip() for op in content.split(',')]
            repeated_content = ','.join(operations * repeat_count)
            
            # Replace in expanded string
            expanded = expanded[:match.start()] + repeated_content + expanded[match.end():]
        
        return expanded
    
    def parse_instruction(self, instruction):
        """Parse instruction into stitch operations"""
        # First expand brackets
        expanded = self.expand_brackets(instruction)
        
        # Split by comma to get individual operations
        operations = [op.strip() for op in expanded.split(',')]
        
        result = []
        for op in operations:
            if not op:
                continue
            
            # Parse stitch type and count
            match = re.match(r'([a-zA-Z]+)([0-9]+)?', op)
            if match:
                stitch_type = match.group(1)
                count = int(match.group(2)) if match.group(2) else 1
                result.append({"stitch": stitch_type, "count": count})
            else:
                self.add_error(f"Invalid stitch operation: {op}", line=0)
        
        return result
    
    def simulate_row(self, row_num, instruction):
        """Simulate a row and return stitch count changes"""
        operations = self.parse_instruction(instruction)
        
        # For now, just return the operations
        # In real knitting, most stitches don't change stitch count
        # Only specific stitches like k2tog, s2k, etc. change stitch count
        start_stitches = self.cast_on if row_num == 1 else self.cast_on  # Simplified
        end_stitches = self.cast_on  # Simplified
        
        return {
            "source_row": row_num,
            "expanded_row_index": row_num,
            "start_stitches": start_stitches,
            "end_stitches": end_stitches,
            "instructions": operations
        }
    
    def compile(self, input_file):
        """Compile a knitting pattern file"""
        self.errors = []
        
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.add_error("File not found", line=None)
            return self.get_result()
        
        # Parse lines
        for i, line in enumerate(lines, 1):
            self.parse_line(line.strip(), i)
        
        # Validate required fields
        if not self.pattern_name:
            self.add_error("Missing pattern name", line=None)
        if self.cast_on is None:
            self.add_error("Missing cast_on", line=None)
        
        # Process rows
        expanded_rows = []
        for row_num, instruction in self.rows:
            row_data = self.simulate_row(row_num, instruction)
            expanded_rows.append(row_data)
        
        return self.get_result(expanded_rows)
    
    def get_result(self, expanded_rows=None):
        """Get final result"""
        if expanded_rows is None:
            expanded_rows = []
        
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": expanded_rows,
            "final_stitch_count": self.cast_on,
            "bind_off": self.bind_off
        }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "compile":
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    compiler = KnittingCompiler()
    result = compiler.compile(input_file)
    
    print(json.dumps(result, indent=2))
    
    if not result["valid"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
