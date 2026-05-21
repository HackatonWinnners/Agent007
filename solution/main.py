#!/usr/bin/env python3
import sys

def uppercase_filter(input_text):
    return input_text.upper()

def lowercase_filter(input_text):
    return input_text.lower()

def main():
    input_text = sys.stdin.read()
    if len(sys.argv) > 1 and sys.argv[1] == "uppercase":
        print(uppercasecase_filter(input_text), end='')
    elif len(sys.argv) > 1:
        print("Invalid argument. Use 'uppercase' or 'lowercase'.")
    else:
        print("Usage: python3 solution/main.py [uppercase|lowercase]")

if __name__ == "__main__":
    main()