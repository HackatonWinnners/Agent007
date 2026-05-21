# Toy CLI Spec

Build `solution/main.py` so that:
- `python3 solution/main.py uppercase` reads stdin and prints uppercase to stdout, exit 0.
- `python3 solution/main.py reverse` reads stdin and prints each line reversed, exit 0.
- Any other subcommand prints `error: unknown command` to stderr, exit 2.
- Empty stdin -> empty stdout, exit 0.
