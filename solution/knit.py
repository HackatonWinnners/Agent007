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
        self.line_errors = {}
        
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
        
        # Remove comments
        if '#' in line:
            # Handle comment logic properly
            comment_start = line.find('#')
            # Check if quote is open
            quote_count = line[:comment_start].count('"')
            if quote_count % 2 == 0:  # Not inside quotes
                line = line[:comment_start].rstrip()
            
        if not line:
            return
        
        # Parse pattern line
        pattern_match = re.match(r'^pattern\s+"(.*)"$', line)
        if pattern_match:
            if self.pattern_name is not None:
                self.add_error("DUPLICATE_PATTERN", "Duplicate pattern declaration.", line_num, None)
            else:
                self.pattern_name = pattern_match.group(1)
            return
        
        # Parse cast_on line
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            if self.cast_on is not None:
                self.add_error("DUPLICATE_CAST_ON", "Duplicate cast_on declaration.", line_num, None)
            else:
                self.cast_on = int(cast_on_match.group(1))
            return
        
        # Parse bind_off line
        bind_off_match = re.match(r'^bind_off$', line)
        if bind_off_match:
            if self.bind_off:
                self.add_error("DUPLICATE_BIND_OFF", "Duplicate bind_off declaration.", line_num, None)
            else:
                self.bind_off = True
            return
        
        # Parse row line
        row_match = re.match(r'^row\s+(\d+):\s*(.*)$', line)
        if row_match:
            row_num = int(row_match.group(1))
            instructions = row_match.group(2)
            self.source_rows.append({
                "line": line_num,
                "row_number": row_num,
                "instructions": instructions
            })
            return
        
        # Parse repeat line
        repeat_match = re.match(r'^repeat\s+rows\s+(\d+)-(\d+)\s+x(\d+)$', line)
        if repeat_match:
            self.source_rows.append({
                "line": line_num,
                "type": "repeat",
                "start": int(repeat_match.group(1)),
                "end": int(repeat_match.group(2)),
                "count": int(repeat_match.group(3))
            })
            return
        
        self.add_error("UNKNOWN_STATEMENT", "Unknown statement.", line_num, None)
        
    def compile(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            self.add_error("UNKNOWN_STATEMENT", f"Error reading file: {str(e)}", None, None)
            self.print_result()
            return
        
        # Parse all lines
        for i, line in enumerate(lines, 1):
            self.parse_line(line, i)
        
        # Validate required fields
        if self.pattern_name is None:
            self.add_error("MISSING_PATTERN", "Missing pattern declaration.", None, None)
        
        if self.cast_on is None:
            self.add_error("MISSING_CAST_ON", "Missing cast_on declaration.", None, None)
        
        # Process rows
        self.process_rows()
        
        # Simulate stitch counts
        self.simulate_stitches()
        
        self.print_result()
        
    def process_rows(self):
        # Simple processing for now
        pass
        
    def simulate_stitches(self):
        # Simple simulation
        if self.cast_on is not None:
            self.final_stitch_count = self.cast_on
        else:
            self.final_stitch_count = None
        
    def print_result(self):
        result = {
            "pattern_name": self.pattern_name,
            "cast_on": self.cast_on,
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "expanded_rows": self.expanded_rows,
            "final_stitch_count": self.final_stitch_count if hasattr(self, 'final_stitch_count') else None,
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