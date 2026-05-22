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
        self.line_number = 0
        self.source_rows = {}
        self.expanded_rows = []
        self.valid = True
        
    def parse_line(self, line, line_num):
        self.line_number = line_num
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
        
        # Parse statement
        parts = line.split(None, 1)
        keyword = parts[0]
        
        if keyword == 'pattern':
            self._parse_pattern(line, parts)
        elif keyword == 'cast_on':
            self._parse_cast_on(line, parts)
        elif keyword == 'bind_off':
            self._parse_bind_off(line, parts)
        elif keyword == 'row':
            self._parse_row(line, parts)
        elif keyword == 'repeat':
            self._parse_repeat(line, parts)
        else:
            self.errors.append({
                'type': 'error',
                'code': 'UNKNOWN_STATEMENT',
                'message': 'Unknown statement.',
                'line': line_num,
                'row': None
            })
    
    def _parse_pattern(self, line, parts):
        if len(parts) < 2:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_PATTERN',
                'message': 'Malformed pattern declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        pattern_line = parts[1]
        if not (pattern_line.startswith('"') and pattern_line.endswith('"')):
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_PATTERN',
                'message': 'Malformed pattern declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        if self.pattern_name is not None:
            self.errors.append({
                'type': 'error',
                'code': 'DUPLICATE_PATTERN',
                'message': 'Duplicate pattern declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        self.pattern_name = pattern_line[1:-1]
    
    def _parse_cast_on(self, line, parts):
        if len(parts) < 2:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_CAST_ON',
                'message': 'Malformed cast_on declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        try:
            value = int(parts[1])
            if value <= 0:
                self.errors.append({
                    'type': 'error',
                    'code': 'MALFORMED_CAST_ON',
                    'message': 'Malformed cast_on declaration.',
                    'line': self.line_number,
                    'row': None
                })
                return
            
            if self.cast_on is not None:
                self.errors.append({
                    'type': 'error',
                    'code': 'DUPLICATE_CAST_ON',
                    'message': 'Duplicate cast_on declaration.',
                    'line': self.line_number,
                    'row': None
                })
                return
            
            self.cast_on = value
        except ValueError:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_CAST_ON',
                'message': 'Malformed cast_on declaration.',
                'line': self.line_number,
                'row': None
            })
    
    def _parse_bind_off(self, line, parts):
        if len(parts) > 1:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_BIND_OFF',
                'message': 'Malformed bind_off declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        if self.bind_off:
            self.errors.append({
                'type': 'error',
                'code': 'DUPLICATE_BIND_OFF',
                'message': 'Duplicate bind_off declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        self.bind_off = True
    
    def _parse_row(self, line, parts):
        if len(parts) < 2:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_ROW',
                'message': 'Malformed row declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        row_line = parts[1]
        
        # Parse row header
        row_match = re.match(r'^([0-9]+):(.*)$', row_line)
        if not row_match:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_ROW',
                'message': 'Malformed row declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        row_num = int(row_match.group(1))
        instructions = row_match.group(2).strip()
        
        if not instructions:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_ROW',
                'message': 'Malformed row declaration.',
                'line': self.line_number,
                'row': row_num
            })
            return
        
        # Check for duplicate or out-of-order rows
        if row_num in self.source_rows:
            self.errors.append({
                'type': 'error',
                'code': 'DUPLICATE_ROW',
                'message': f'Duplicate row number {row_num}.',
                'line': self.line_number,
                'row': row_num
            })
            return
        
        # Check if row number is valid
        if row_num <= 0:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_ROW',
                'message': 'Malformed row declaration.',
                'line': self.line_number,
                'row': row_num
            })
            return
        
        # Store row
        self.source_rows[row_num] = {
            'line': self.line_number,
            'instructions': instructions
        }
    
    def _parse_repeat(self, line, parts):
        if len(parts) < 2:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_REPEAT',
                'message': 'Malformed repeat declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        repeat_line = parts[1]
        # Check if it matches the expected pattern
        match = re.match(r'^rows\s+([0-9]+)-([0-9]+)\s+x([0-9]+)$', repeat_line)
        if not match:
            self.errors.append({
                'type': 'error',
                'code': 'MALFORMED_REPEAT',
                'message': 'Malformed repeat declaration.',
                'line': self.line_number,
                'row': None
            })
            return
        
        start_row = int(match.group(1))
        end_row = int(match.group(2))
        count = int(match.group(3))
        
        if start_row <= 0 or end_row <= 0 or start_row > end_row:
            self.errors.append({
                'type': 'error',
                'code': 'INVALID_REPEAT_RANGE',
                'message': 'Repeat range references rows that do not exist.',
                'line': self.line_number,
                'row': None
            })
            return
        
        if count <= 0:
            self.errors.append({
                'type': 'error',
                'code': 'INVALID_REPEAT_COUNT',
                'message': 'Repeat count must be a positive integer.',
                'line': self.line_number,
                'row': None
            })
            return
        
        # Store repeat
        self.source_rows['repeat'] = {
            'line': self.line_number,
            'start': start_row,
            'end': end_row,
            'count': count
        }
    
    def validate_and_expand(self):
        # Validate required fields
        if self.pattern_name is None:
            self.errors.append({
                'type': 'error',
                'code': 'MISSING_PATTERN',
                'message': 'Missing pattern declaration.',
                'line': None,
                'row': None
            })
            self.valid = False
        
        if self.cast_on is None:
            self.errors.append({
                'type': 'error',
                'code': 'MISSING_CAST_ON',
                'message': 'Missing cast_on declaration.',
                'line': None,
                'row': None
            })
            self.valid = False
        
        # Check for duplicate pattern and cast_on
        if self.pattern_name is not None and self.pattern_name == '':
            # This is valid, but we need to check if there are duplicates
            pass
        
        # Expand rows
        self._expand_rows()
        
        # Simulate stitch counts
        self._simulate_stitches()
        
        # Sort errors by line number
        self.errors.sort(key=lambda e: (e['line'] if e['line'] is not None else float('inf'), e['code']))
    
    def _expand_rows(self):
        # Simple expansion for now
        pass
    
    def _simulate_stitches(self):
        # Simple simulation for now
        pass
    
    def compile(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse all lines
            for i, line in enumerate(lines, 1):
                self.parse_line(line, i)
            
            # Validate and expand
            self.validate_and_expand()
            
            # Build result
            result = {
                'pattern_name': self.pattern_name,
                'cast_on': self.cast_on,
                'valid': self.valid,
                'errors': self.errors,
                'expanded_rows': self.expanded_rows,
                'final_stitch_count': None,
                'bind_off': self.bind_off
            }
            
            print(json.dumps(result, separators=(',', ':')))
            
        except Exception as e:
            print(json.dumps({'pattern_name': None, 'cast_on': None, 'valid': False, 'errors': [{'type': 'error', 'code': 'UNKNOWN_ERROR', 'message': str(e), 'line': None, 'row': None}], 'expanded_rows': [], 'final_stitch_count': None, 'bind_off': False}), file=sys.stderr)
            sys.exit(1)


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    compiler = KnitCompiler()
    compiler.compile(sys.argv[2])


if __name__ == "__main__":
    main()
