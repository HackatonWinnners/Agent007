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
        self.source_rows = {}
        self.expanded_rows = []
        self.line_number = 0
        self.cast_on_line = None
        self.pattern_line = None
        self.bind_off_line = None
        self.cast_on_after_row = False
        self.bind_off_after_row = False
        self.row_count = 0
        self.row_numbers = set()
        self.duplicate_rows = set()
        self.out_of_order_rows = set()
        self.row_repeats = []
        self.bind_off_position = None
        
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
        line = line.rstrip()
        # Handle comments
        comment_start = line.find('#')
        if comment_start != -1:
            # Check if quote is open before comment
            quote_count = line[:comment_start].count('"')
            if quote_count % 2 == 0:  # Not inside quotes
                line = line[:comment_start]
        
        line = line.strip()
        if not line:
            return
        
        # Parse pattern
        pattern_match = re.match(r'^pattern\s+"(.*)"$', line)
        if pattern_match:
            if self.pattern_name is not None:
                self.add_error("DUPLICATE_PATTERN", "Duplicate pattern declaration.", line_num, None)
            else:
                self.pattern_name = pattern_match.group(1)
                self.pattern_line = line_num
            return
        
        # Parse cast_on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            if self.cast_on is not None:
                self.add_error("DUPLICATE_CAST_ON", "Duplicate cast_on declaration.", line_num, None)
            else:
                try:
                    value = int(cast_on_match.group(1))
                    if value <= 0:
                        self.add_error("MALFORMED_CAST_ON", "Cast on must be a positive integer.", line_num, None)
                    else:
                        self.cast_on = value
                        self.cast_on_line = line_num
                except ValueError:
                    self.add_error("MALFORMED_CAST_ON", "Cast on must be a positive integer.", line_num, None)
            return
        
        # Parse bind_off
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            if self.bind_off:
                self.add_error("DUPLICATE_BIND_OFF", "Duplicate bind_off declaration.", line_num, None)
            else:
                self.bind_off = True
                self.bind_off_line = line_num
            return
        
        # Parse rows
        row_match = re.match(r'^row\s+(\d+)\s*:\s*(.*)$', line)
        if row_match:
            try:
                row_num = int(row_match.group(1))
                instructions = row_match.group(2).strip()
                
                # Check for empty instructions
                if not instructions:
                    self.add_error("MALFORMED_ROW", "Row must contain at least one instruction.", line_num, row_num)
                    return
                
                # Check for duplicate row numbers
                if row_num in self.row_numbers:
                    self.add_error("DUPLICATE_ROW", f"Duplicate row number {row_num}.", line_num, row_num)
                    self.duplicate_rows.add(row_num)
                elif row_num in self.source_rows:
                    # This is a row that was already processed but not in current rows
                    self.add_error("DUPLICATE_ROW", f"Duplicate row number {row_num}.", line_num, row_num)
                    self.duplicate_rows.add(row_num)
                else:
                    # Check for out of order rows
                    if self.row_numbers and row_num < max(self.row_numbers):
                        self.add_error("OUT_OF_ORDER_ROW", f"Row {row_num} is out of order.", line_num, row_num)
                        self.out_of_order_rows.add(row_num)
                    
                self.source_rows[row_num] = {
                    "line": line_num,
                    "instructions": instructions,
                    "row_num": row_num
                }
                self.row_numbers.add(row_num)
                
            except ValueError:
                self.add_error("MALFORMED_ROW", "Invalid row number.", line_num, None)
            return
        
        # Parse row repeats
        repeat_match = re.match(r'^repeat\s+rows\s+(\d+)-(\d+)\s+x(\d+)$', line)
        if repeat_match:
            try:
                start = int(repeat_match.group(1))
                end = int(repeat_match.group(2))
                count = int(repeat_match.group(3))
                
                if start <= 0 or end <= 0:
                    self.add_error("INVALID_REPEAT_RANGE", "Repeat range must use positive integers.", line_num, None)
                elif start > end:
                    self.add_error("INVALID_REPEAT_RANGE", "Repeat range start must be less than or equal to end.", line_num, None)
                elif count <= 0:
                    self.add_error("INVALID_REPEAT_COUNT", "Repeat count must be a positive integer.", line_num, None)
                else:
                    self.row_repeats.append({
                        "line": line_num,
                        "start": start,
                        "end": end,
                        "count": count
                    })
            except ValueError:
                self.add_error("MALFORMED_REPEAT", "Invalid repeat statement syntax.", line_num, None)
            return
        
        # Unknown statement
        self.add_error("UNKNOWN_STATEMENT", "Unknown statement.", line_num, None)
        
    def validate_and_expand_rows(self):
        # Validate that all rows referenced in repeats exist
        for repeat in self.row_repeats:
            start = repeat["start"]
            end = repeat["end"]
            # Check if all rows in range exist
            for i in range(start, end + 1):
                if i not in self.source_rows:
                    self.add_error("INVALID_REPEAT_RANGE", "Repeat range references rows that do not exist.", repeat["line"], None)
                    break
        
        # Build expanded row sequence
        expanded_sequence = []
        
        # Add original rows
        for row_num in sorted(self.source_rows.keys()):
            if row_num not in self.duplicate_rows and row_num not in self.out_of_order_rows:
                expanded_sequence.append(row_num)
        
        # Add repeated rows
        for repeat in self.row_repeats:
            start = repeat["start"]
            end = repeat["end"]
            count = repeat["count"]
            
            # Add the range count times
            for _ in range(count):
                for i in range(start, end + 1):
                    if i in self.source_rows and i not in self.duplicate_rows and i not in self.out_of_order_rows:
                        expanded_sequence.append(i)
        
        return expanded_sequence
        
    def parse_instructions(self, instructions):
        # Simple parser for instruction lists
        # Split by comma and handle whitespace
        parts = [part.strip() for part in instructions.split(',') if part.strip()]
        result = []
        
        for part in parts:
            if not part:
                continue
            
            # Check for valid stitch operations
            stitch_match = re.match(r'^(k|p|yo|k2tog|ssk|inc|dec)(\d*)$', part)
            if stitch_match:
                stitch = stitch_match.group(1)
                count = int(stitch_match.group(2)) if stitch_match.group(2) else 1
                result.append({"stitch": stitch, "count": count})
            else:
                self.add_error("UNKNOWN_STITCH", f"Unknown stitch {part}.", None, None)
        
        return result
        
    def simulate_stitches(self, expanded_sequence):
        if self.cast_on is None:
            return 0
        
        stitch_count = self.cast_on
        final_stitch_count = stitch_count
        
        for i, row_num in enumerate(expanded_sequence):
            row_data = self.source_rows[row_num]
            instructions = self.parse_instructions(row_data["instructions"])
            
            # Check for errors in parsing
            if len(self.errors) > 0:
                break
            
            # Simulate the row
            start_stitches = stitch_count
            for instruction in instructions:
                stitch = instruction["stitch"]
                count = instruction["count"]
                
                if stitch == "k" or stitch == "p":
                    # These consume and produce the same number of stitches
                    if stitch_count < count:
                        self.add_error("STITCH_UNDERFLOW", f"Row {row_num} consumes more stitches than available.", row_data["line"], row_num)
                        return stitch_count
                    stitch_count -= count
                    stitch_count += count
                elif stitch == "yo":
                    # Yarn over produces 1 stitch
                    stitch_count += 1
                elif stitch == "k2tog" or stitch == "ssk":
                    # These consume 2 stitches and produce 1
                    if stitch_count < 2:
                        self.add_error("STITCH_UNDERFLOW", f"Row {row_num} consumes more stitches than available.", row_data["line"], row_num)
                        return stitch_count
                    stitch_count -= 2
                    stitch_count += 1
                elif stitch == "inc":
                    # Increase produces 2 stitches from 1
                    stitch_count += 1
                elif stitch == "dec":
                    # Decrease produces 1 stitch from 2
                    if stitch_count < 2:
                        self.add_error("STITCH_UNDERFLOW", f"Row {row_num} consumes more stitches than available.", row_data["line"], row_num)
                        return stitch_count
                    stitch_count -= 2
                    stitch_count += 1
                
                # Check for stitch overflow
                if stitch_count > 10000:
                    self.add_error("STITCH_OVERFLOW", f"Row {row_num} produces more than 10,000 stitches.", row_data["line"], row_num)
                    return stitch_count
            
            final_stitch_count = stitch_count
            
        return final_stitch_count
        
    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            result = {
                "errors": [{"type": "error", "code": "FILE_NOT_FOUND", "message": "File not found.", "line": None, "row": None}],
                "valid": False
            }
            print(json.dumps(result))
            sys.exit(2)
        
        # Parse all lines
        for i, line in enumerate(lines):
            self.line_number = i + 1
            self.parse_line(line, self.line_number)
        
        # Validate required statements
        if self.pattern_name is None:
            self.add_error("MISSING_PATTERN", "Missing pattern declaration.", None, None)
        
        if self.cast_on is None:
            self.add_error("MISSING_CAST_ON", "Missing cast_on declaration.", None, None)
        
        # Check for cast_on after rows
        if self.cast_on_line is not None and self.row_numbers:
            max_row = max(self.row_numbers)
            if self.cast_on_line > max_row:
                self.add_error("CAST_ON_OUT_OF_ORDER", "Cast on appears after row declarations.", self.cast_on_line, None)
        elif self.cast_on_line is not None and not self.row_numbers:
            # No rows, so cast_on is valid
            pass
        
        # Check for bind_off after rows
        if self.bind_off and self.row_numbers:
            max_row = max(self.row_numbers)
            if self.bind_off_line and self.bind_off_line > max_row:
                self.add_error("BIND_OFF_OUT_OF_ORDER", "Bind off appears after row declarations.", self.bind_off_line, None)
        
        # Validate row repeats
        expanded_sequence = self.validate_and_expand_rows()
        
        # Build expanded rows
        if len(self.errors) == 0:
            stitch_count = self.cast_on if self.cast_on is not None else 0
            
            for i, row_num in enumerate(expanded_sequence):
                row_data = self.source_rows[row_num]
                instructions = self.parse_instructions(row_data["instructions"])
                
                # Create expanded row object
                expanded_row = {
                    "expanded_row_index": i + 1,
                    "source_row": row_num,
                    "instructions": instructions,
                    "start_stitches": stitch_count,
                    "end_stitches": stitch_count
                }
                
                self.expanded_rows.append(expanded_row)
                
                # Update stitch count for next row
                # This is a simplified version - we'll do proper simulation later
                
            # Do proper stitch simulation
            final_stitch_count = self.simulate_stitches(expanded_sequence)
            
            # Update end_stitches in expanded rows
            if len(self.expanded_rows) > 0:
                # This is a simplified approach - we'll fix this later
                pass
        else:
            final_stitch_count = None
        
        # Build result
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
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
