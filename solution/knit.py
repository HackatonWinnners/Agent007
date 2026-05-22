#!/usr/bin/env python3

import sys
import json
import re

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    errors = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse pattern name
        pattern_match = re.match(r'^pattern\s+(.+)$', line)
        if pattern_match:
            pattern_name = pattern_match.group(1).strip().strip('"')
            continue
        
        # Parse cast_on
        cast_on_match = re.match(r'^cast_on\s+(\d+)$', line)
        if cast_on_match:
            cast_on = int(cast_on_match.group(1))
            continue
        
        # Parse rows
        row_match = re.match(r'^row\s+(\d+):\s+(.+)$', line)
        if row_match:
            row_number = int(row_match.group(1))
            row_content = row_match.group(2).strip()
            rows.append((row_number, row_content))
            continue
    
    return pattern_name, cast_on, rows, errors

def expand_brackets(row_content):
    # Handle bracketed repeats like [k1, p1] x2
    bracket_pattern = r'\[(.*?)\]\s+x\s+(\d+)'
    matches = re.findall(bracket_pattern, row_content)
    
    if matches:
        expanded = row_content
        for match in matches:
            content, repeat_count = match
            repeat_count = int(repeat_count)
            # Replace the bracketed content with repeated content
            expanded = re.sub(r'\[' + re.escape(content) + r'\]\s+x\s+' + str(repeat_count), 
                             content * repeat_count, expanded)
        return expanded
    
    return row_content

def parse_row_content(row_content):
    # Simple parsing of stitch commands
    # This is a simplified version - in a real implementation we'd parse more carefully
    stitches = []
    # Split by comma and space to get individual commands
    parts = row_content.split(', ')
    for part in parts:
        part = part.strip()
        if part:
            stitches.append(part)
    return stitches

def simulate_stitch_count(stitches, initial_count):
    count = initial_count
    for stitch in stitches:
        if stitch.startswith('k') or stitch.startswith('p'):
            count += 1  # Each stitch adds 1 stitch
    return count

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        pattern_name, cast_on, rows, errors = parse_knit_file(input_file)
        
        # Process rows
        expanded_rows = []
        current_stitch_count = cast_on
        
        for row_number, row_content in rows:
            # Expand brackets
            expanded_content = expand_brackets(row_content)
            
            # Parse the expanded content
            stitches = parse_row_content(expanded_content)
            
            # Simulate stitch count
            new_stitch_count = simulate_stitch_count(stitches, current_stitch_count)
            current_stitch_count = new_stitch_count
            
            # Add to expanded rows
            expanded_rows.append({
                'row_number': row_number,
                'content': expanded_content,
                'stitch_count': new_stitch_count
            })
        
        # Determine bind_off
        bind_off = False
        if rows and len(rows) > 0:
            # If there are rows, check if we should bind off
            # This is a simplified check - in reality we'd need to check the pattern
            bind_off = True
        
        result = {
            'pattern_name': pattern_name,
            'cast_on': cast_on,
            'valid': len(errors) == 0,
            'errors': errors,
            'expanded_rows': expanded_rows,
            'final_stitch_count': current_stitch_count,
            'bind_off': bind_off
        }
        
        print(json.dumps(result))
        
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
