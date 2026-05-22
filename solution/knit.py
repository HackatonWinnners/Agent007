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
        
    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        parts = line.split(None, 1)
        keyword = parts[0]
        
        if keyword == 'pattern':
            if len(parts) > 1:
                # Remove quotes
                value = parts[1].strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                self.pattern_name = value
        elif keyword == 'cast_on':
            if len(parts) > 1:
                try:
                    self.cast_on = int(parts[1])
                except ValueError:
                    self.errors.append(f"Invalid cast_on value: {parts[1]}")
        elif keyword == 'row':
            if len(parts) > 1:
                self.rows.append(parts[1])
        elif keyword == 'bind_off':
            self.bind_off = True
        
    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    self.parse_line(line)
        except FileNotFoundError:
            print(json.dumps({"errors": [f"File not found: {filename}"]}), file=sys.stderr)
            sys.exit(1)
        
        # Validate required fields
        if self.pattern_name is None:
            self.errors.append("Missing pattern name")
        if self.cast_on is None:
            self.errors.append("Missing cast_on value")
        
        # Simulate rows
        expanded_rows = []
        stitch_count = self.cast_on
        
        for i, row in enumerate(self.rows):
            # Simple simulation - just track stitch count
            expanded_rows.append({
                "expanded_row_index": i + 1,
                "instructions": row,
                "source_row": row,
                "start_stitches": stitch_count,
                "end_stitches": stitch_count,
                "stitch_operations": []
            })
            
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": expanded_rows,
            "final_stitch_count": stitch_count,
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
