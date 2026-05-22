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
        
        if line.startswith('pattern "'):
            pattern_name = line.split('"')[1]
        elif line.startswith('cast_on '):
            cast_on = int(line.split()[1])
        elif line.startswith('row '):
            # Parse row definition
            # Example: row 1: k1, p1
            row_match = re.match(r'row ([0-9]+):(.*)', line)
            if row_match:
                row_number = int(row_match.group(1))
                content = row_match.group(2).strip()
                rows.append({
                    'row_number': row_number,
                    'content': content
                })
    
    return {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'rows': rows,
        'errors': errors
    }

def expand_bracket_repeats(row_content):
    # Handle bracket repeats like [k1, p1] x2
    repeat_pattern = r'\[(.*?)\]\s*x\s*(\d+)'
    matches = re.findall(repeat_pattern, row_content)
    
    if matches:
        # Find the first match and expand it
        for match in matches:
            inner_content = match[0]
            repeat_count = int(match[1])
            # Replace the bracketed content with expanded version
            expanded = ', '.join([inner_content] * repeat_count)
            row_content = re.sub(repeat_pattern, expanded, row_content, 1)
    
    return row_content


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        parsed = parse_knit_file(input_file)
        
        # Process rows
        expanded_rows = []
        current_stitch_count = parsed['cast_on']
        
        for i, row in enumerate(parsed['rows']):
            # Expand bracket repeats
            expanded_content = expand_bracket_repeats(row['content'])
            
            # For now, just add the row as-is
            expanded_rows.append({
                'row_number': row['row_number'],
                'content': expanded_content,
                'stitch_count': current_stitch_count,
                'start_stitches': 0,
                'end_stitches': 0,
                'instructions': [],
                'source_row': row['content'],
                'expanded_row_index': i
            })
            
        # Simple bind_off logic
        bind_off = False
        if parsed['rows']:
            bind_off = True  # Simple heuristic
        
        result = {
            'pattern_name': parsed['pattern_name'],
            'cast_on': parsed['cast_on'],
            'valid': len(parsed['errors']) == 0,
            'errors': parsed['errors'],
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
