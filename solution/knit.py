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
        
        # Pattern name
        pattern_match = re.match(r'^pattern\s+(.+)$', line)
        if pattern_match:
            self.pattern_name = pattern_match.group(1).strip('"\'')
            return True
        
        # Cast on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            self.cast_on = int(cast_on_match.group(1))
            return True
        
        # Rows
        row_match = re.match(r'^row\s+(.+)$', line)
        if row_match:
            self.rows.append(row_match.group(1))
            return True
        
        # Bind off
        if line == 'bind_off':
            self.bind_off = True
            return True
        
        return False

    def parse(self, lines):
        for i, line in enumerate(lines):
            if not self.parse_line(line):
                self.errors.append(f"Invalid syntax at line {i+1}: {line.strip()}")

    def expand_rows(self):
        # For now, just add the rows as they are
        if not self.rows:
            # If no rows, add a row with cast_on stitches
            self.expanded_rows.append({
                'source_row': '',
                'start_stitches': self.cast_on,
                'end_stitches': self.cast_on,
                'expanded_row_index': 0,
                'instructions': []
            })
        else:
            for i, row in enumerate(self.rows):
                self.expanded_rows.append({
                    'source_row': row,
                    'start_stitches': self.cast_on,
                    'end_stitches': self.cast_on,
                    'expanded_row_index': i,
                    'instructions': []
                })

    def simulate(self):
        # Simple simulation - no changes
        pass

    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(json.dumps({'errors': ['File not found']}), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(json.dumps({'errors': [f'Error reading file: {str(e)}']}), file=sys.stderr)
            sys.exit(1)

        self.parse(lines)
        
        if self.errors:
            print(json.dumps({'errors': self.errors}))
            sys.exit(1)
        
        if self.pattern_name is None:
            self.errors.append('Missing pattern name')
        
        if self.cast_on is None:
            self.errors.append('Missing cast_on')
        
        if self.errors:
            print(json.dumps({'errors': self.errors}))
            sys.exit(1)
        
        self.expand_rows()
        self.simulate()
        
        result = {
            'pattern_name': self.pattern_name,
            'cast_on': self.cast_on,
            'bind_off': self.bind_off,
            'expanded_rows': self.expanded_rows
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
