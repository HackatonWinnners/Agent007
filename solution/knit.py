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
        self.row_numbers = set()
        self.row_order = []
        
    def add_error(self, code, message, line=None, row=None):
        error = {
            "type": "error",
            "code": code,
            "message": message,
            "line": line,
            "row": row
        }
        self.errors.append(error)
        
    def parse_line(self, line, line_num):
        line = line.strip()
        if not line or line.startswith('#'):
            return
        
        # Remove comment
        if '#' in line:
            comment_start = line.find('#')
            # Check if quote is open
            quote_count = line[:comment_start].count('"')
            if quote_count % 2 == 0:
                line = line[:comment_start].rstrip()
                
        if not line:
            return
        
        # Parse pattern
        if line.startswith('pattern '):
            pattern_match = re.match(r'^pattern "(.*)"$', line)
            if not pattern_match:
                self.add_error('MALFORMED_PATTERN', 'Malformed pattern declaration.', line_num, None)
                return
            self.pattern_name = pattern_match.group(1)
            return
        
        # Parse cast_on
        if line.startswith('cast_on '):
            cast_on_match = re.match(r'^cast_on ([0-9]+)$', line)
            if not cast_on_match:
                self.add_error('MALFORMED_CAST_ON', 'Malformed cast-on declaration.', line_num, None)
                return
            self.cast_on = int(cast_on_match.group(1))
            return
        
        # Parse row
        if line.startswith('row '):
            row_match = re.match(r'^row ([0-9]+):(.*)$', line)
            if not row_match:
                self.add_error('MALFORMED_ROW', 'Malformed row declaration.', line_num, None)
                return
            
            row_num = int(row_match.group(1))
            instructions = row_match.group(2).strip()
            
            # Check for duplicate or out-of-order rows
            if row_num in self.row_numbers:
                self.add_error('DUPLICATE_ROW', f'Duplicate row number {row_num}.', line_num, row_num)
                return
            
            if self.row_order and row_num < max(self.row_order):
                self.add_error('OUT_OF_ORDER_ROW', f'Out of order row number {row_num}.', line_num, row_num)
                return
            
            # Add to row tracking
            self.row_numbers.add(row_num)
            self.row_order.append(row_num)
            
            # Parse instructions
            if not instructions:
                self.add_error('MALFORMED_ROW', 'Row has no instructions.', line_num, row_num)
                return
            
            # Store row
            self.rows.append({
                'line': line_num,
                'row_num': row_num,
                'instructions': instructions
            })
            return
        
        # Parse repeat
        if line.startswith('repeat '):
            repeat_match = re.match(r'^repeat rows ([0-9]+)-([0-9]+) x([0-9]+)$', line)
            if not repeat_match:
                self.add_error('MALFORMED_REPEAT', 'Malformed repeat statement.', line_num, None)
                return
            
            start = int(repeat_match.group(1))
            end = int(repeat_match.group(2))
            count = int(repeat_match.group(3))
            
            if start <= 0 or end <= 0:
                self.add_error('INVALID_REPEAT_RANGE', 'Repeat range contains non-positive row numbers.', line_num, None)
                return
            
            if start > end:
                self.add_error('INVALID_REPEAT_RANGE', 'Repeat range is invalid.', line_num, None)
                return
            
            if count <= 0:
                self.add_error('INVALID_REPEAT_COUNT', 'Repeat count must be a positive integer.', line_num, None)
                return
            
            # Check if all rows in range exist
            for i in range(start, end + 1):
                if i not in self.row_numbers:
                    self.add_error('INVALID_REPEAT_RANGE', 'Repeat range references rows that do not exist.', line_num, None)
                    return
            
            # Store repeat
            self.rows.append({
                'line': line_num,
                'repeat': True,
                'start': start,
                'end': end,
                'count': count
            })
            return
        
        # Parse bind_off
        if line == 'bind_off':
            self.bind_off = True
            return
        
        # Unknown statement
        self.add_error('UNKNOWN_STATEMENT', 'Unknown statement.', line_num, None)
        
    def expand_rows(self):
        # Expand rows including repeats
        expanded = []
        
        # Add all rows
        for row in self.rows:
            if 'repeat' in row:
                # Handle repeat
                start = row['start']
                end = row['end']
                count = row['count']
                
                # Add repeated rows
                for i in range(count):
                    for j in range(start, end + 1):
                        # Find the original row
                        for orig_row in self.rows:
                            if orig_row.get('row_num') == j:
                                expanded.append(orig_row)
                                break
            else:
                expanded.append(row)
        
        self.expanded_rows = expanded
        
    def simulate_stitches(self):
        if not self.cast_on:
            return
        
        # Simulate stitch counts
        current_stitches = self.cast_on
        
        for i, row in enumerate(self.expanded_rows):
            if 'repeat' in row:
                continue
            
            # Process instructions
            instructions = row['instructions']
            instruction_items = [item.strip() for item in instructions.split(',') if item.strip()]
            
            for instruction in instruction_items:
                # Parse instruction
                inst_match = re.match(r'^([a-z]+)([0-9]*)$', instruction)
                if not inst_match:
                    continue
                
                stitch_type = inst_match.group(1)
                stitch_count = inst_match.group(2)
                
                if stitch_count:
                    count = int(stitch_count)
                else:
                    count = 1
                
                # Apply stitch semantics
                if stitch_type == 'k' or stitch_type == 'p':
                    if count > current_stitches:
                        self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                        return
                    current_stitches -= count
                elif stitch_type == 'yo':
                    current_stitches += 1
                elif stitch_type == 'k2tog' or stitch_type == 'ssk' or stitch_type == 'dec':
                    if 2 > current_stitches:
                        self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                        return
                    current_stitches -= 1
                elif stitch_type == 'inc':
                    current_stitches += 1
                
                if current_stitches > 10000:
                    self.add_error('STITCH_OVERFLOW', 'Row produces too many stitches.', row['line'], row['row_num'])
                    return
        
        return current_stitches
        
    def compile(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
        
        # Parse all lines
        for i, line in enumerate(lines):
            self.parse_line(line, i + 1)
        
        # Validate required declarations
        if not self.pattern_name:
            self.add_error('MISSING_PATTERN', 'Missing pattern declaration.', None, None)
        
        if not self.cast_on:
            self.add_error('MISSING_CAST_ON', 'Missing cast-on declaration.', None, None)
        
        # Check for errors
        valid = len(self.errors) == 0
        
        # Expand rows
        self.expand_rows()
        
        # Simulate stitches
        final_stitch_count = None
        if valid:
            final_stitch_count = self.simulate_stitches()
        
        # Finalize result
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": valid,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": final_stitch_count,
            "bind_off": self.bind_off
        }
        
        print(json.dumps(result))
        
        if not valid:
            sys.exit(1)
        else:
            sys.exit(0)


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnitCompiler()
    compiler.compile(sys.argv[2])


if __name__ == "__main__":
    main()
