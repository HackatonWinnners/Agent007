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
            pattern_name = line.split('pattern "', 1)[1].rstrip('"')
        elif line.startswith('cast_on '):
            cast_on = int(line.split('cast_on ')[1])
        elif line.startswith('row '):
            # Parse row definition
            # Example: row 1: [k1, p1] x2
            row_match = re.match(r'row ([0-9]+):\s*(.*)', line)
            if row_match:
                row_num = int(row_match.group(1))
                row_content = row_match.group(2)
                rows.append({'row_num': row_num, 'content': row_content})
    
    # Process rows to expand repeats
    expanded_rows = []
    final_stitch_count = cast_on
    bind_off = False
    
    for row in rows:
        row_num = row['row_num']
        content = row['content']
        
        # Handle bracketed repeats
        expanded_content = expand_bracket_repeats(content)
        
        # Count stitches
        stitch_count = count_stitches(expanded_content)
        
        # Add to expanded rows
        expanded_rows.append({
            'row_num': row_num,
            'content': expanded_content,
            'stitch_count': stitch_count
        })
        
        final_stitch_count = stitch_count
        
        # Check if bind_off should be set (if last row)
        if row_num == max(r['row_num'] for r in rows) if rows else 1:
            bind_off = True
    
    return {
        'pattern_name': pattern_name,
        'cast_on': cast_on,
        'valid': len(errors) == 0,
        'errors': errors,
        'expanded_rows': expanded_rows,
        'final_stitch_count': final_stitch_count,
        'bind_off': bind_off
    }

def expand_bracket_repeats(content):
    # Handle [k1, p1] x2 pattern
    bracket_pattern = r'\[([^\]]+)\]\s*x\s*(\d+)'
    def replace_repeat(match):
        inner_content = match.group(1)
        repeat_count = int(match.group(2))
        return (inner_content + ' ') * repeat_count
    
    expanded = re.sub(bracket_pattern, replace_repeat, content)
    return expanded.strip()

def count_stitches(content):
    # Count stitches in content
    # Example: k1 p1 k2
    stitches = 0
    for part in content.split():
        if part.startswith(('k', 'p', 's', 't', 'm', 'c', 'b', 'h', 'd', 'f', 'g', 'j', 'l', 'z', 'x', 'v', 'n', 'm')):
            # Extract number
            num_match = re.search(r'\d+', part)
            if num_match:
                stitches += int(num_match.group())
            else:
                stitches += 1
    return stitches


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'compile':
        print("Usage: python3 knit.py compile <input_file>", file=sys.stderr)
        sys.exit(2)
    
    input_file = sys.argv[2]
    
    try:
        result = parse_knit_file(input_file)
        print(json.dumps(result))
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
