#!/usr/bin/env python3

import sys
import json
import re

def parse_knit_file(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    pattern_name = "Unknown Pattern"
    cast_on = 0
    rows = []
    errors = []
    
    for line in lines:
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on '):
            cast_on = int(line.split()[1])
        elif line.startswith('row '):
            # Parse row definition
            # Example: row 1: k1, p1, k1
            parts = line.split(':', 1)
            if len(parts) == 2:
                row_num = int(parts[0].split()[1])
                content = parts[1].strip()
                rows.append({'row_number': row_num, 'content': content})
    
    return pattern_name, cast_on, rows, errors

def expand_bracket_repeats(content):
    # Handle bracket repeats like [k1, p1] x2
    bracket_pattern = r'\[(.*?)\] x(\d+)'
    matches = re.findall(bracket_pattern, content)
    
    if matches:
        # Replace bracketed repeat with expanded content
        expanded = content
        for match in matches:
            inner_content, repeat_count = match
            repeat_count = int(repeat_count)
            expanded = expanded.replace(f'[{inner_content}] x{repeat_count}', 
                                      f'{inner_content} ' * repeat_count)
        return expanded.strip()
    return content

def simulate_row(row_content, stitch_count):
    # Simple simulation - count stitches
    stitches = row_content.split(', ')
    count = 0
    for stitch in stitches:
        if stitch.startswith('k') or stitch.startswith('p'):
            # For simplicity, assume each stitch is 1 stitch
            count += 1
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
        
        for row in rows:
            row_number = row['row_number']
            content = row['content']
            
            # Expand bracket repeats
            expanded_content = expand_bracket_repeats(content)
            
            # Simulate stitch count
            stitch_count = simulate_row(expanded_content, current_stitch_count)
            
            # For now, just return the row structure
            expanded_rows.append({
                'expanded_row_index': len(expanded_rows),
                'source_row': row_number,
                'start_stitches': current_stitch_count,
                'instructions': expanded_content,
                'end_stitches': current_stitch_count + stitch_count
            })
            
            # Update stitch count
            current_stitch_count += stitch_count
        
        # Determine bind_off
        bind_off = False
        if rows and rows[-1]['row_number'] > 0:
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
