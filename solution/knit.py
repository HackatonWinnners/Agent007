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
        
        parts = line.split()
        if not parts:
            return None
        
        keyword = parts[0]
        
        if keyword == 'pattern':
            self.pattern_name = ' '.join(parts[1:])
        elif keyword == 'cast_on':
            try:
                self.cast_on = int(parts[1])
            except (ValueError, IndexError):
                self.errors.append(f"Invalid cast_on value: {' '.join(parts[1:])}")
        elif keyword == 'row':
            # Parse row definition
            row_def = ' '.join(parts[1:])
            self.rows.append(row_def)
        elif keyword == 'bind_off':
            self.bind_off = True
        
    def parse(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except IOError:
            self.errors.append(f"Could not read file: {filename}")
            return
        
        for line in lines:
            self.parse_line(line)
        
    def simulate_row(self, row_def, stitch_count):
        # Simple simulation - just count stitches
        # This is a simplified version - real implementation would be more complex
        return stitch_count
    
    def expand_rows(self):
        # For now, just return the rows as-is
        expanded_rows = []
        for i, row_def in enumerate(self.rows):
            expanded_rows.append({
                "expanded_row_index": i,
                "instructions": row_def,
                "source_row": i,
                "start_stitches": self.cast_on if i == 0 else 0,
                "end_stitches": self.cast_on if i == 0 else 0
            })
        return expanded_rows
    
    def compile(self, filename):
        self.parse(filename)
        
        # Validate required fields
        if self.pattern_name is None:
            self.errors.append("Missing pattern name")
        if self.cast_on is None:
            self.errors.append("Missing cast_on value")
        
        # Simulate rows
        expanded_rows = self.expand_rows()
        
        # Calculate final stitch count
        final_stitch_count = self.cast_on
        if expanded_rows:
            final_stitch_count = expanded_rows[-1]["end_stitches"]
        
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": expanded_rows,
            "final_stitch_count": final_stitch_count,
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
