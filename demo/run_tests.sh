#!/usr/bin/env bash
set -uo pipefail
PASS=0; FAIL=0
check() {
  local name="$1" expected_stdout="$2" expected_code="$3" stdin="$4"; shift 4
  local out code
  out=$(printf '%s' "$stdin" | "$@" 2>/dev/null); code=$?
  if [[ "$out" == "$expected_stdout" && $code -eq $expected_code ]]; then
    PASS=$((PASS+1)); echo "ok   - $name"
  else
    FAIL=$((FAIL+1)); echo "fail - $name (got '$out' code $code)"
  fi
}
check "uppercase" "HELLO" 0 "hello" python3 ../solution/main.py uppercase
check "reverse" "olleh" 0 "hello" python3 ../solution/main.py reverse
check "unknown" "" 2 "x" python3 ../solution/main.py whatever
check "empty" "" 0 "" python3 ../solution/main.py uppercase
echo "score: $PASS/$((PASS+FAIL))"
