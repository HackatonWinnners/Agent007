#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) != 2:
        print("error: unknown command", file=sys.stderr)
        sys.exit(2)
    
    command = sys.argv[1]
    
    if command == "uppercase":
        process_lines(lambda line: line.upper())
    elif command == "reverse":
        process_lines(lambda line: line[::-1])
    else:
        print("error: unknown command", file=sys.stderr)
        sys.exit(2)

def process_lines(transform):
    for line in sys.stdin:
        print(transform(line.rstrip('\n')))

if __name__ == "__main__":
    main()