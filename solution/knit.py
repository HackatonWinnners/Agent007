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
        self.cast_on_valid = False
        self.pattern_valid = False
        self.bind_off_valid = False
        
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
            self.parse_pattern(line, line_num)
            return
        
        # Parse cast_on
        if line.startswith('cast_on '):
            self.parse_cast_on(line, line_num)
            return
        
        # Parse row
        if line.startswith('row '):
            self.parse_row(line, line_num)
            return
        
        # Parse repeat
        if line.startswith('repeat '):
            self.parse_repeat(line, line_num)
            return
        
        # Parse bind_off
        if line == 'bind_off':
            self.parse_bind_off(line, line_num)
            return
        
        # Unknown statement
        self.add_error('UNKNOWN_STATEMENT', 'Unknown statement.', line_num, None)
        
    def parse_pattern(self, line, line_num):
        pattern_match = re.match(r'^pattern "(.*)"$', line)
        if not pattern_match:
            self.add_error('MALFORMED_PATTERN', 'Malformed pattern declaration.', line_num, None)
            return
        
        if self.pattern_valid:
            self.add_error('DUPLICATE_PATTERN', 'Duplicate pattern declaration.', line_num, None)
            return
        
        self.pattern_name = pattern_match.group(1)
        self.pattern_valid = True
        
    def parse_cast_on(self, line, line_num):
        cast_on_match = re.match(r'^cast_on ([0-9]+)$', line)
        if not cast_on_match:
            self.add_error('MALFORMED_CAST_ON', 'Malformed cast-on declaration.', line_num, None)
            return
        
        cast_on_value = int(cast_on_match.group(1))
        if cast_on_value <= 0:
            self.add_error('MALFORMED_CAST_ON', 'Malformed cast-on declaration.', line_num, None)
            return
        
        if self.cast_on_valid:
            self.add_error('DUPLICATE_CAST_ON', 'Duplicate cast-on declaration.', line_num, None)
            return
        
        self.cast_on = cast_on_value
        self.cast_on_valid = True
        
    def parse_row(self, line, line_num):
        # Parse row header
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
        
        # Check for empty instruction items
        instruction_items = [item.strip() for item in instructions.split(',') if item.strip()]
        if len(instruction_items) == 0:
            self.add_error('MALFORMED_ROW', 'Row has no instructions.', line_num, row_num)
            return
        
        # Validate instructions
        for item in instruction_items:
            if not self.is_valid_stitch(item):
                self.add_error('UNKNOWN_STITCH', f'Unknown stitch {item}.', line_num, row_num)
                
        # Store row
        self.rows.append({
            'line': line_num,
            'row_num': row_num,
            'instructions': instructions,
            'instruction_items': instruction_items
        })
        
    def is_valid_stitch(self, stitch):
        # Check if it's a valid stitch
        stitch_match = re.match(r'^([a-z]+)([0-9]*)$', stitch)
        if not stitch_match:
            return False
        
        stitch_type = stitch_match.group(1)
        stitch_count = stitch_match.group(2)
        
        valid_stitches = ['k', 'p', 'yo', 'k2tog', 'ssk', 'inc', 'dec']
        if stitch_type not in valid_stitches:
            return False
        
        if stitch_count and not stitch_count.isdigit():
            return False
        
        if stitch_count and int(stitch_count) <= 0:
            return False
        
        return True
        
    def parse_repeat(self, line, line_num):
        # Parse repeat statement
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
        
    def parse_bind_off(self, line, line_num):
        if self.bind_off_valid:
            self.add_error('DUPLICATE_BIND_OFF', 'Duplicate bind-off declaration.', line_num, None)
            return
        
        self.bind_off = True
        self.bind_off_valid = True
        
    def expand_rows(self):
        # Expand rows including repeats
        expanded = []
        
        # Add original rows
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
        if not self.cast_on_valid:
            return
        
        # Simulate stitch counts
        current_stitches = self.cast_on
        
        for i, row in enumerate(self.expanded_rows):
            if 'repeat' in row:
                continue
            
            # Process instructions
            instructions = row['instruction_items']
            start_stitches = current_stitches
            end_stitches = current_stitches
            
            for instruction in instructions:
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
                    if count > end_stitches:
                        self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                        return
                    end_stitches -= count
                elif stitch_type == 'yo':
                    end_stitches += 1
                elif stitch_type == 'k2tog' or stitch_type == 'ssk' or stitch_type == 'dec':
                    if 2 > end_stitches:
                        self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                        return
                    end_stitches -= 1
                elif stitch_type == 'inc':
                    end_stitches += 1
                
                if end_stitches > 10000:
                    self.add_error('STITCH_OVERFLOW', 'Row produces too many stitches.', row['line'], row['row_num'])
                    return
            
            current_stitches = end_stitches
        
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
        if not self.pattern_valid:
            self.add_error('MISSING_PATTERN', 'Missing pattern declaration.', None, None)
        
        if not self.cast_on_valid:
            self.add_error('MISSING_CAST_ON', 'Missing cast-on declaration.', None, None)
        
        # Check for errors
        valid = len(self.errors) == 0
        
        # Expand rows
        self.expand_rows()
        
        # Simulate stitches
        if valid:
            self.simulate_stitches()
            
        # Build final result with correct format
        result = {
            "pattern_name": self.pattern_name if self.pattern_valid else None,
            "cast_on": self.cast_on if self.cast_on_valid else None,
            "valid": valid,
            "errors": self.errors,
            "expanded_rows": [],
            "final_stitch_count": None,
            "bind_off": self.bind_off
        }
        
        # Build expanded_rows with correct format
        if valid and self.cast_on_valid:
            current_stitches = self.cast_on
            expanded_rows = []
            
            for i, row in enumerate(self.expanded_rows):
                if 'repeat' in row:
                    continue
                
                # Process instructions
                instructions = row['instruction_items']
                start_stitches = current_stitches
                end_stitches = current_stitches
                
                for instruction in instructions:
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
                        if count > end_stitches:
                            self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                            break
                        end_stitches -= count
                    elif stitch_type == 'yo':
                        end_stitches += 1
                    elif stitch_type == 'k2tog' or stitch_type == 'ssk' or stitch_type == 'dec':
                        if 2 > end_stitches:
                            self.add_error('STITCH_UNDERFLOW', 'Row consumes more stitches than available.', row['line'], row['row_num'])
                            break
                        end_stitches -= 1
                    elif stitch_type == 'inc':
                        end_stitches += 1
                    
                    if end_stitches > 10000:
                        self.add_error('STITCH_OVERFLOW', 'Row produces too many stitches.', row['line'], row['row_num'])
                        break
                
                # Update current stitches
                current_stitches = end_stitches
                
                # Add to expanded rows with correct format
                expanded_rows.append({
                    "end_stitches": end_stitches,
                    "expanded_row_index": i,
                    "source_row": row,
                    "start_stitches": start_stitches
                })
            
            result["expanded_rows"] = expanded_rows
            result["final_stitch_count"] = current_stitches
        
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
