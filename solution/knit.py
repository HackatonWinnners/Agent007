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
        self.expanded_rows = []
        
    def parse_line(self, line, line_num):
        line = line.strip()
        if not line or line.startswith('#'):
            return
        
        # Parse pattern line
        pattern_match = re.match(r'^pattern\s+(.+)$', line)
        if pattern_match:
            self.pattern_name = pattern_match.group(1).strip('"')
            return
        
        # Parse cast_on line
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            self.cast_on = int(cast_on_match.group(1))
            return
        
        # Parse bind_off line
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            self.bind_off = True
            return
        
        # Parse row line
        row_match = re.match(r'^row\s+(.+)$', line)
        if row_match:
            self.rows.append(row_match.group(1))
            return
        
        self.errors.append(f"Invalid syntax on line {line_num}: {line}")
        
    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            self.print_result()
            return
        
        for i, line in enumerate(lines, 1):
            self.parse_line(line, i)
        
        # Validate required fields
        if not self.pattern_name:
            self.errors.append("Missing pattern name")
        if self.cast_on is None:
            self.errors.append("Missing cast_on count")
        
        # Simulate rows
        self.simulate_rows()
        
        self.print_result()
        
    def simulate_rows(self):
        # Simple simulation - just track stitch count
        stitch_count = self.cast_on
        self.expanded_rows = []
        
        for i, row in enumerate(self.rows):
            # For now, just track the stitch count
            self.expanded_rows.append({
                "row_number": i + 1,
                "start_stitches": stitch_count,
                "end_stitches": stitch_count,
                "stitch_operations": row
            })
    
    def print_result(self):
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": self.cast_on,
            "bind_off": self.bind_off
        }
        print(json.dumps(result))


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnitCompiler()
    compiler.compile(sys.argv[2])


if __name__ == "__main__":
    main()