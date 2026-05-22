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
        self.source_rows = []
        self.expanded_rows = []

    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Parse pattern name
        pattern_match = re.match(r'^pattern\s+(.+)$', line)
        if pattern_match:
            self.pattern_name = pattern_match.group(1).strip().strip('"\'')
            return True
        
        # Parse cast_on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            self.cast_on = int(cast_on_match.group(1))
            return True
        
        # Parse bind_off
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            self.bind_off = True
            return True
        
        # Parse rows
        if line.startswith('row'):
            # This is a row definition
            self.rows.append(line)
            return True
        
        return None

    def parse(self, lines):
        for line in lines:
            self.parse_line(line)

    def expand_row(self, row_str):
        # Simple implementation for now
        return row_str

    def simulate_stitches(self):
        # Simple simulation - just return the cast_on for now
        if self.cast_on is not None:
            return self.cast_on
        return 0

    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            result = {
                "errors": ["File not found"],
                "valid": False
            }
            print(json.dumps(result))
            sys.exit(1)
        
        self.parse(lines)
        
        # Build expanded rows
        expanded_rows = []
        stitch_count = self.cast_on if self.cast_on is not None else 0
        
        for i, row in enumerate(self.rows):
            expanded_rows.append({
                "expanded_row_index": i + 1,
                "start_stitches": stitch_count,
                "end_stitches": stitch_count,
                "source_row": row,
                "instructions": [row]
            })
            
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "bind_off": self.bind_off,
            "expanded_rows": expanded_rows,
            "final_stitch_count": stitch_count,
            "errors": self.errors,
            "valid": len(self.errors) == 0
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
