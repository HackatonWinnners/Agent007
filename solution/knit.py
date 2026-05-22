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
            self.pattern_name = pattern_match.group(1).strip().strip('"\'')
            return True
        
        # Cast on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            self.cast_on = int(cast_on_match.group(1))
            return True
        
        # Bind off
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            self.bind_off = True
            return True
        
        # Row definition
        row_match = re.match(r'^row\s+(.+)$', line)
        if row_match:
            self.rows.append(row_match.group(1).strip())
            return True
        
        return False

    def expand_row(self, row_str):
        # Simple expansion - just return the row as-is for now
        return row_str

    def simulate_row(self, row_str, current_stitches):
        # Simple simulation - just return the current stitch count
        return current_stitches

    def expand_rows(self):
        # Expand rows with repeats
        expanded = []
        for i, row in enumerate(self.rows):
            expanded.append(row)
        return expanded

    def simulate_stitches(self):
        # Simple simulation
        if not self.rows:
            return [self.cast_on] if self.cast_on is not None else [0]
        
        # For now, just return the cast_on count
        return [self.cast_on] if self.cast_on is not None else [0]

    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                self.parse_line(line)
            
            # Expand rows
            expanded_rows = self.expand_rows()
            
            # Simulate stitch counts
            stitch_counts = self.simulate_stitches()
            
            # Build result
            result = {
                "pattern_name": self.pattern_name,
                "cast_on": self.cast_on,
                "bind_off": self.bind_off,
                "errors": self.errors,
                "valid": len(self.errors) == 0,
                "final_stitch_count": stitch_counts[-1] if stitch_counts else None,
                "expanded_rows": []
            }
            
            # Add expanded rows with proper structure
            for i, row in enumerate(expanded_rows):
                result["expanded_rows"].append({
                    "source_row": row,
                    "expanded_row_index": i,
                    "start_stitches": self.cast_on if i == 0 else stitch_counts[i-1],
                    "end_stitches": stitch_counts[i] if i < len(stitch_counts) else self.cast_on,
                    "instructions": [row]
                })
            
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
