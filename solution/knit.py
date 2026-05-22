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
        
    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Parse pattern name
        pattern_match = re.match(r'^pattern\s+(.+)$', line)
        if pattern_match:
            self.pattern_name = pattern_match.group(1).strip('"\'')
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
        
        return False
    
    def parse(self, lines):
        for line in lines:
            self.parse_line(line)
        
    def expand_rows(self):
        # For now, just return the rows as-is
        expanded_rows = []
        for i, row in enumerate(self.rows):
            expanded_rows.append({
                'expanded_row_index': i,
                'source_row': row,
                'start_stitches': self.cast_on,
                'end_stitches': self.cast_on,
                'instructions': [row]
            })
        return expanded_rows
    
    def simulate(self):
        # Simple simulation - just return the cast_on count
        return self.cast_on
    
    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            self.parse(lines)
            
            # Validate
            if self.pattern_name is None:
                self.errors.append('Missing pattern name')
            if self.cast_on is None:
                self.errors.append('Missing cast_on')
            
            # Build result
            result = {
                'pattern_name': self.pattern_name,
                'cast_on': self.cast_on,
                'bind_off': self.bind_off,
                'valid': len(self.errors) == 0,
                'errors': self.errors,
                'final_stitch_count': self.cast_on if self.cast_on is not None else 0,
                'expanded_rows': self.expand_rows()
            }
            
            print(json.dumps(result))
            
        except FileNotFoundError:
            print("Error: File not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnitCompiler()
    compiler.compile(sys.argv[2])


if __name__ == "__main__":
    main()
