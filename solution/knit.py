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
        elif keyword == 'bind_off':
            self.bind_off = True
        elif keyword == 'row':
            if len(parts) > 1:
                self.rows.append(parts[1])
        
    def simulate_row(self, row_content, stitch_count):
        # Simple simulation - just count stitches
        operations = row_content.split()
        new_stitch_count = stitch_count
        
        for op in operations:
            if op == 'k':
                new_stitch_count += 0  # knit - no change
            elif op == 'p':
                new_stitch_count += 0  # purl - no change
            elif op == 'yo':
                new_stitch_count += 1  # yarn over - increases by 1
            elif op == 'k2tog':
                new_stitch_count -= 1  # knit two together - decreases by 1
            elif op == 'ssk':
                new_stitch_count -= 1  # slip, slip, knit - decreases by 1
            elif op == 'inc':
                new_stitch_count += 1  # increase - increases by 1
            elif op == 'dec':
                new_stitch_count -= 1  # decrease - decreases by 1
        
        return new_stitch_count
    
    def expand_rows(self):
        expanded_rows = []
        current_stitch_count = self.cast_on
        
        for i, row_content in enumerate(self.rows):
            # Simple expansion - just add the row as-is
            expanded_rows.append({
                'expanded_row_index': i + 1,
                'instructions': row_content,
                'source_row': i + 1,
                'start_stitches': current_stitch_count,
                'end_stitches': current_stitch_count
            })
            
            # Simulate the row
            current_stitch_count = self.simulate_row(row_content, current_stitch_count)
            
        return expanded_rows
    
    def compile(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                self.parse_line(line)
                
            # Validate required fields
            if self.pattern_name is None:
                self.errors.append("Missing pattern name")
            if self.cast_on is None:
                self.errors.append("Missing cast_on value")
                
            # Expand rows
            expanded_rows = self.expand_rows()
            
            # Build result
            result = {
                'pattern_name': self.pattern_name,
                'cast_on': self.cast_on,
                'valid': len(self.errors) == 0,
                'errors': self.errors,
                'expanded_rows': expanded_rows,
                'final_stitch_count': self.cast_on if len(expanded_rows) == 0 else expanded_rows[-1]['end_stitches'] if expanded_rows else self.cast_on,
                'bind_off': self.bind_off
            }
            
            print(json.dumps(result, separators=(',', ':')))
            
        except Exception as e:
            print(json.dumps({'pattern_name': None, 'cast_on': None, 'valid': False, 'errors': [str(e)], 'expanded_rows': [], 'final_stitch_count': 0, 'bind_off': False}), file=sys.stderr)
            sys.exit(1)


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnitCompiler()
    compiler.compile(sys.argv[2])


if __name__ == "__main__":
    main()
