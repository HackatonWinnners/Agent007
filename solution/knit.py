#!/usr/bin/env python3

import sys
import json
import os
import re

class KnittingCompiler:
    def __init__(self):
        self.pattern_name = None
        self.cast_on = None
        self.bind_off = False
        self.rows = []
        self.repeats = []
        
    def parse(self, input_file):
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('pattern'):
                self.pattern_name = line.split(' ', 1)[1].strip('"')
            elif line.startswith('cast_on'):
                self.cast_on = int(line.split()[1])
            elif line.startswith('bind_off'):
                self.bind_off = True
            elif line.startswith('row'):
                # Parse row definition
                row_match = re.match(r'row\s+(\d+):\s+(.*)', line)
                if row_match:
                    row_num = int(row_match.group(1))
                    instructions = row_match.group(2)
                    self.rows.append((row_num, instructions))
            elif line.startswith('repeat'):
                # Parse repeat definition
                repeat_match = re.match(r'repeat\s+rows\s+(\d+)-(\d+)\s+x(\d+)', line)
                if repeat_match:
                    start_row = int(repeat_match.group(1))
                    end_row = int(repeat_match.group(2))
                    times = int(repeat_match.group(3))
                    self.repeats.append((start_row, end_row, times))
            i += 1
        
    def expand_repeats(self):
        expanded_rows = []
        
        # First, add all original rows
        for row_num, instructions in self.rows:
            expanded_rows.append((row_num, instructions, 0))  # 0 = original row
        
        # Then add repeated rows
        for start_row, end_row, times in self.repeats:
            # Get the rows to repeat
            rows_to_repeat = [(r_num, instr) for r_num, instr in self.rows if start_row <= r_num <= end_row]
            
            # Add repeated versions
            for i in range(times):
                for row_num, instructions in rows_to_repeat:
                    expanded_rows.append((row_num, instructions, i + 1))  # i+1 = repeat index
        
        return expanded_rows
    
    def parse_instructions(self, instructions):
        # Split by comma and parse each instruction
        parts = [part.strip() for part in instructions.split(',')]
        parsed = []
        
        for part in parts:
            # Match stitch type and count
            match = re.match(r'([a-zA-Z]+)(\d*)', part)
            if match:
                stitch_type = match.group(1)
                count = int(match.group(2)) if match.group(2) else 1
                parsed.append({'stitch': stitch_type, 'count': count})
        
        return parsed
    
    def simulate_row(self, instructions, start_stitches):
        # For each stitch type, calculate the consumption and production
        consumed = 0
        produced = 0
        
        for instruction in instructions:
            stitch_type = instruction['stitch']
            count = instruction['count']
            
            if stitch_type == 'k':  # knit
                consumed += count  # consume count stitches
                produced += count  # produce count stitches
            elif stitch_type == 'p':  # purl
                consumed += count  # consume count stitches
                produced += count  # produce count stitches
            elif stitch_type == 'yo':  # yarn over
                consumed += 0  # consume 0 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'k2tog':  # knit two together
                consumed += 2  # consume 2 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'p2tog':  # purl two together
                consumed += 2  # consume 2 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 's2k':  # slip, knit
                consumed += 1  # consume 1 stitch
                produced += 1  # produce 1 stitch
            elif stitch_type == 's2p':  # slip, purl
                consumed += 1  # consume 1 stitch
                produced += 1  # produce 1 stitch
            elif stitch_type == 'm1':  # make one
                consumed += 0  # consume 0 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'm1l':  # make one left
                consumed += 0  # consume 0 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'm1r':  # make one right
                consumed += 0  # consume 0 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'ssk':  # slip, slip, knit
                consumed += 2  # consume 2 stitches
                produced += 1  # produce 1 stitch
            elif stitch_type == 'kfb':  # knit front and back
                consumed += 1  # consume 1 stitch
                produced += 2  # produce 2 stitches
            elif stitch_type == 'pfb':  # purl front and back
                consumed += 1  # consume 1 stitch
                produced += 2  # produce 2 stitches
            elif stitch_type == 'sl':  # slip
                consumed += 1  # consume 1 stitch
                produced += 0  # produce 0 stitches
            elif stitch_type == 'rep':  # repeat
                # This is handled differently in the parsing
                pass
            
        # Calculate net change
        net_change = produced - consumed
        end_stitches = start_stitches + net_change
        
        return {
            'start_stitches': start_stitches,
            'end_stitches': end_stitches,
            'consumed': consumed,
            'produced': produced,
            'net_change': net_change
        }
    
    def compile(self, input_file):
        try:
            self.parse(input_file)
            
            # Validate basic structure
            if not self.pattern_name or self.cast_on is None:
                return {
                    'pattern_name': self.pattern_name,
                    'cast_on': self.cast_on,
                    'valid': False,
                    'errors': ['Missing pattern name or cast_on'],
                    'expanded_rows': [],
                    'final_stitch_count': 0,
                    'bind_off': self.bind_off
                }
            
            # Expand repeats
            expanded_rows = self.expand_repeats()
            
            # Simulate each row
            result_rows = []
            current_stitches = self.cast_on
            
            for i, (row_num, instructions, repeat_index) in enumerate(expanded_rows):
                parsed_instructions = self.parse_instructions(instructions)
                
                # Simulate the row
                row_result = self.simulate_row(parsed_instructions, current_stitches)
                
                # Build the result row
                result_row = {
                    'source_row': row_num,
                    'expanded_row_index': i + 1,
                    'start_stitches': row_result['start_stitches'],
                    'end_stitches': row_result['end_stitches'],
                    'instructions': parsed_instructions
                }
                
                result_rows.append(result_row)
                current_stitches = row_result['end_stitches']
            
            return {
                'pattern_name': self.pattern_name,
                'cast_on': self.cast_on,
                'valid': True,
                'errors': [],
                'expanded_rows': result_rows,
                'final_stitch_count': current_stitches,
                'bind_off': self.bind_off
            }
            
        except Exception as e:
            return {
                'pattern_name': self.pattern_name,
                'cast_on': self.cast_on,
                'valid': False,
                'errors': [str(e)],
                'expanded_rows': [],
                'final_stitch_count': 0,
                'bind_off': self.bind_off
            }


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print('Usage: python3 knit.py compile <input_file>', file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    if not os.path.exists(input_file):
        print(f'Error: File {input_file} not found', file=sys.stderr)
        sys.exit(1)
    
    compiler = KnittingCompiler()
    result = compiler.compile(input_file)
    
    print(json.dumps(result, indent=2))
    
    if not result['valid']:
        sys.exit(1)

if __name__ == '__main__':
    main()
