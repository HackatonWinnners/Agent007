import sys

def main():
    if len(sys.argv) != 2:
        print("error: unknown command", file=sys.stderr)
        sys.exit(2)
    
    command = sys.argv[1]
    
    if command == "uppercase":
        for line in sys.stdin:
            print(line.upper(), end='')
    elif command == "reverse":
        for line in sys.stdin:
            print(line[::-1], end='')
    else:
        print("error: unknown command", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()