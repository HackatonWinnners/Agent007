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
        self.final_stitch_count = None
        self.cast_on_line = None
        self.rows_after_cast_on = False
        self.bind_off_line = None
        self.rows_after_bind_off = False
        self.row_numbers = set()
        self.row_repeat_statements = []
        self.source_row_order = []
        self.expanded_row_order = []
        self.valid = True
        
    def parse_file(self, file_path):
        with open(file_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]
        
        # Parse lines
        for i, line in enumerate(lines, 1):
            # Remove comments
            if '#' in line:
                # Handle comments properly - need to track quotes
                line_no_comment = self.remove_comments(line)
                if line_no_comment is None:
                    # Malformed line with unclosed quote
                    self.errors.append({
                        "type": "error",
                        "code": "MALFORMED_PATTERN",
                        "message": "Malformed pattern declaration.",
                        "line": i,
                        "row": None
                    })
                    continue
                line = line_no_comment
            
            if not line.strip():
                continue
            
            # Parse pattern
            if line.startswith('pattern "'):
                if self.pattern_name is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_PATTERN",
                        "message": "Duplicate pattern declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        self.pattern_name = line.split('pattern "', 1)[1].rsplit('"', 1)[0]
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_PATTERN",
                            "message": "Malformed pattern declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse cast_on
            elif line.startswith('cast_on '):
                if self.cast_on is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_CAST_ON",
                        "message": "Duplicate cast_on declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        value = int(line.split('cast_on ')[1])
                        if value <= 0:
                            raise ValueError()
                        self.cast_on = value
                        self.cast_on_line = i
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_CAST_ON",
                            "message": "Malformed cast_on declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse row
            elif line.startswith('row '):
                if self.bind_off_line is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "BIND_OFF_OUT_OF_ORDER",
                        "message": "Statement appears after bind_off.",
                        "line": i,
                        "row": None
                    })
                
                # Check if this is a valid row line
                if ':' not in line:
                    self.errors.append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "message": "Malformed row declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    try:
                        row_part, content = line.split(':', 1)
                        row_num = int(row_part.split()[1])
                        
                        # Check for valid row number
                        if row_num <= 0:
                            self.errors.append({
                                "type": "error",
                                "code": "MALFORMED_ROW",
                                "message": "Malformed row declaration.",
                                "line": i,
                                "row": None
                            })
                        else:
                            # Check for duplicate row
                            if row_num in self.row_numbers:
                                self.errors.append({
                                    "type": "error",
                                    "code": "DUPLICATE_ROW",
                                    "message": f"Duplicate row number {row_num}.",
                                    "line": i,
                                    "row": row_num
                                })
                            else:
                                # Check for out of order row
                                if self.source_row_order and row_num < max(self.source_row_order):
                                    self.errors.append({
                                        "type": "error",
                                        "code": "OUT_OF_ORDER_ROW",
                                        "message": f"Row {row_num} is out of order.",
                                        "line": i,
                                        "row": row_num
                                    })
                                else:
                                    self.row_numbers.add(row_num)
                                    self.source_rows[row_num] = content.strip()
                                    self.source_row_order.append(row_num)
                    except:
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_ROW",
                            "message": "Malformed row declaration.",
                            "line": i,
                            "row": None
                        })
            
            # Parse bind_off
            elif line == 'bind_off':
                if self.bind_off_line is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "DUPLICATE_BIND_OFF",
                        "message": "Duplicate bind_off declaration.",
                        "line": i,
                        "row": None
                    })
                else:
                    self.bind_off = True
                    self.bind_off_line = i
            
            # Parse repeat
            elif line.startswith('repeat rows '):
                if self.bind_off_line is not None:
                    self.errors.append({
                        "type": "error",
                        "code": "BIND_OFF_OUT_OF_ORDER",
                        "message": "Statement appears after bind_off.",
                        "line": i,
                        "row": None
                    })
                
                try:
                    # Parse repeat statement
                    parts = line.split()
                    if len(parts) != 5 or parts[0] != 'repeat' or parts[1] != 'rows' or parts[3] != 'x':
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_REPEAT",
                            "message": "Malformed repeat statement.",
                            "line": i,
                            "row": None
                        })
                    else:
                        range_part = parts[2]
                        count_part = parts[4]
                        
                        # Check for valid range
                        if '-' not in range_part:
                            self.errors.append({
                                "type": "error",
                                "code": "MALFORMED_REPEAT",
                                "message": "Malformed repeat statement.",
                                "line": i,
                                "row": None
                            })
                        else:
                            start_str, end_str = range_part.split('-')
                            try:
                                start = int(start_str)
                                end = int(end_str)
                                count = int(count_part)
                                
                                if start <= 0 or end <= 0 or start > end:
                                    self.errors.append({
                                        "type": "error",
                                        "code": "INVALID_REPEAT_RANGE",
                                        "message": "Repeat range references rows that do not exist.",
                                        "line": i,
                                        "row": None
                                    })
                                elif count <= 0:
                                    self.errors.append({
                                        "type": "error",
                                        "code": "INVALID_REPEAT_COUNT",
                                        "message": "Repeat count must be a positive integer.",
                                        "line": i,
                                        "row": None
                                    })
                                else:
                                    self.row_repeat_statements.append({
                                        "line": i,
                                        "start": start,
                                        "end": end,
                                        "count": count
                                    })
                            except ValueError:
                                self.errors.append({
                                    "type": "error",
                                    "code": "INVALID_REPEAT_COUNT",
                                    "message": "Repeat count must be a positive integer.",
                                    "line": i,
                                    "row": None
                                })
                except:
                    self.errors.append({
                        "type": "error",
                        "code": "MALFORMED_REPEAT",
                        "message": "Malformed repeat statement.",
                        "line": i,
                        "row": None
                    })
            
            # Unknown statement
            else:
                self.errors.append({
                    "type": "error",
                    "code": "UNKNOWN_STATEMENT",
                    "message": "Unknown statement.",
                    "line": i,
                    "row": None
                })
        
        # Validate required fields
        if self.pattern_name is None:
            self.errors.append({
                "type": "error",
                "code": "MISSING_PATTERN",
                "message": "Missing pattern declaration.",
                "line": None,
                "row": None
            })
        
        if self.cast_on is None:
            self.errors.append({
                "type": "error",
                "code": "MISSING_CAST_ON",
                "message": "Missing cast_on declaration.",
                "line": None,
                "row": None
            })
        
        # Check for cast_on out of order
        if self.cast_on is not None and self.rows_after_cast_on:
            self.errors.append({
                "type": "error",
                "code": "CAST_ON_OUT_OF_ORDER",
                "message": "cast_on appears after a row declaration.",
                "line": self.cast_on_line,
                "row": None
            })
        
        # Process rows
        self.expand_rows()
        
        # Calculate final stitch count
        if self.cast_on is not None and self.expanded_rows:
            self.final_stitch_count = self.expanded_rows[-1]["end_stitches"]
        elif self.cast_on is not None:
            self.final_stitch_count = self.cast_on
        
        return self.get_result()
    
    def remove_comments(self, line):
        """Remove comments from line, respecting quoted strings"""
        in_quotes = False
        quote_char = None
        result = ""
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if not in_quotes and char == '"':
                in_quotes = True
                quote_char = char
                result += char
            elif in_quotes and char == quote_char:
                in_quotes = False
                quote_char = None
                result += char
            elif not in_quotes and char == '#':
                break  # Ignore everything after #
            else:
                result += char
            
            i += 1
        
        return result
    
    def parse_instructions(self, content):
        """Parse instruction content into a list of instruction objects"""
        instructions = []
        
        # Handle bracketed repeats
        # First, we need to properly parse the instruction list
        try:
            # Split by comma to get individual instructions
            parts = [part.strip() for part in content.split(',') if part.strip()]
            
            for part in parts:
                # Check for bracketed repeat
                if part.startswith('[') and part.endswith(']'):
                    # This is a bracketed repeat
                    # Extract the content inside brackets
                    bracket_content = part[1:-1]
                    # Find the x<count> part
                    if ' x' in bracket_content:
                        # This is malformed - bracketed repeat should be at the end
                        self.errors.append({
                            "type": "error",
                            "code": "MALFORMED_ROW",
                            "message": "Malformed row declaration.",
                            "line": None,
                            "row": None
                        })
                        return []
                    else:
                        # Regular bracketed repeat
                        # For now, just add the bracketed content as a single instruction
                        # We'll expand this later
                        instructions.append({
                            "type": "bracketed",
                            "content": bracket_content
                        })
                else:
                    # Regular instruction - parse stitch and count
                    # Match pattern like 'k4', 'yo', 'p10', etc.
                    import re
                    match = re.match(r'^([a-zA-Z]+)(\d+)
    
    def expand_rows(self):
        # Process rows in order
        for row_num in sorted(self.source_rows.keys()):
            content = self.source_rows[row_num]
            instructions = self.parse_instructions(content)
            
            # For now, just add the row with instructions
            self.expanded_rows.append({
                "expanded_row_index": len(self.expanded_rows) + 1,
                "source_row": row_num,
                "instructions": instructions,
                "start_stitches": self.cast_on if len(self.expanded_rows) == 0 else self.expanded_rows[-1]["end_stitches"],
                "end_stitches": self.cast_on if len(self.expanded_rows) == 0 else self.expanded_rows[-1]["end_stitches"]
            })
    
    def get_result(self):
        valid = len(self.errors) == 0
        if not valid:
            self.expanded_rows = []
            self.final_stitch_count = None
        
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": valid,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": self.final_stitch_count,
            "bind_off": self.bind_off
        }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        compiler = KnitCompiler()
        result = compiler.parse_file(input_file)
        print(json.dumps(result))
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
, part)
                    if match:
                        stitch = match.group(1)
                        count = int(match.group(2))
                        instructions.append({
                            "stitch": stitch,
                            "count": count
                        })
                    else:
                        # Single stitch without count (like 'yo')
                        if part.isalpha():
                            instructions.append({
                                "stitch": part,
                                "count": 1
                            })
                        else:
                            # Malformed instruction
                            self.errors.append({
                                "type": "error",
                                "code": "MALFORMED_ROW",
                                "message": "Malformed row declaration.",
                                "line": None,
                                "row": None
                            })
                            return []
        except Exception as e:
            self.errors.append({
                "type": "error",
                "code": "MALFORMED_ROW",
                "message": "Malformed row declaration.",
                "line": None,
                "row": None
            })
            return []
        
        return instructions
    
    def expand_rows(self):
        # Process rows in order
        for row_num in sorted(self.source_rows.keys()):
            content = self.source_rows[row_num]
            instructions = self.parse_instructions(content)
            
            # For now, just add the row with instructions
            self.expanded_rows.append({
                "expanded_row_index": len(self.expanded_rows) + 1,
                "source_row": row_num,
                "instructions": instructions,
                "start_stitches": self.cast_on if len(self.expanded_rows) == 0 else self.expanded_rows[-1]["end_stitches"],
                "end_stitches": self.cast_on if len(self.expanded_rows) == 0 else self.expanded_rows[-1]["end_stitches"]
            })
    
    def get_result(self):
        valid = len(self.errors) == 0
        if not valid:
            self.expanded_rows = []
            self.final_stitch_count = None
        
        return {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": valid,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": self.final_stitch_count,
            "bind_off": self.bind_off
        }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        compiler = KnitCompiler()
        result = compiler.parse_file(input_file)
        print(json.dumps(result))
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
