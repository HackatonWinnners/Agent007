#!/usr/bin/env bash
set -euo pipefail
if ! command -v bun >/dev/null 2>&1; then
  echo "Installing Bun..."
  curl -fsSL https://bun.sh/install | bash
  export PATH="$HOME/.bun/bin:$PATH"
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 required. Install via brew install python or apt." >&2; exit 1
fi
(cd agent && bun install)
if [ ! -f .env ]; then cp .env.example .env; echo "Created .env. Edit it to add FEATHERLESS_API_KEY"; fi
echo "Setup done. Next: edit .env then 'cd agent && bun run src/main.ts --help'"
