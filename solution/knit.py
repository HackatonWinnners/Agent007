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
            self.pattern_name = pattern_match.group(1).strip('"\'')
            return True
        
        # Parse cast_on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            self.cast_on = int(cast_on_match.group(1))
            return True
        
        # Parse rows
        if line.startswith('rows'):
            return True  # Just a marker
        
        # Parse row definition
        row_match = re.match(r'^(\d+)\s+(.*)$', line)
        if row_match:
            row_num = int(row_match.group(1))
            content = row_match.group(2)
            self.rows.append((row_num, content))
            return True
        
        # Parse bind_off
        if line == 'bind_off':
            self.bind_off = True
            return True
        
        return False

    def expand_row(self, row_num, content):
        # Simple expansion - just return the content as-is for now
        return content

    def simulate_row(self, row_num, content, stitch_count):
        # Simple simulation - just return the stitch count
        return stitch_count

    def compile(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse the file
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse pattern name
                pattern_match = re.match(r'^pattern\s+(.+)$', line)
                if pattern_match:
                    self.pattern_name = pattern_match.group(1).strip('"\'')
                    continue
                
                # Parse cast_on
                cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
                if cast_on_match:
                    self.cast_on = int(cast_on_match.group(1))
                    continue
                
                # Parse rows
                if line.startswith('rows'):
                    continue  # Just a marker
                
                # Parse row definition
                row_match = re.match(r'^(\d+)\s+(.*)$', line)
                if row_match:
                    row_num = int(row_match.group(1))
                    content = row_match.group(2)
                    self.rows.append((row_num, content))
                    continue
                
                # Parse bind_off
                if line == 'bind_off':
                    self.bind_off = True
                    continue
                
                # If we get here, it's an unrecognized line
                self.errors.append(f"Unrecognized line {line_num}: {line}")
                
            # Expand rows
            stitch_count = self.cast_on
            for i, (row_num, content) in enumerate(self.rows):
                expanded_content = self.expand_row(row_num, content)
                final_stitch_count = self.simulate_row(row_num, content, stitch_count)
                
                # Build expanded row
                expanded_row = {
                    "expanded_row_index": i,
                    "source_row": row_num,
                    "start_stitches": stitch_count,
                    "end_stitches": final_stitch_count,
                    "instructions": expanded_content
                }
                
                self.expanded_rows.append(expanded_row)
                stitch_count = final_stitch_count
                
            # Build result
            result = {
                "valid": len(self.errors) == 0,
                "errors": self.errors,
                "final_stitch_count": stitch_count,
                "expanded_rows": self.expanded_rows
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
