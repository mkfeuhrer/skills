#!/usr/bin/env bash
# Mechanical gates from CHECKLIST.md. Usage: scripts/validate.sh <skill-name>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: validate.sh <skill-name>}"
DIR="$ROOT/skills/$NAME"
fail=0

gate() { # gate <num> <label> <command...>
  local n="$1" label="$2"; shift 2
  if "$@" >/dev/null 2>&1; then echo "PASS gate $n: $label"; else echo "FAIL gate $n: $label"; fail=1; fi
}

[ -f "$DIR/SKILL.md" ] || { echo "FAIL: SKILL.md missing"; exit 1; }

head -20 "$DIR/SKILL.md" | grep -q '^name:' &&
  head -40 "$DIR/SKILL.md" | grep -q '^description:'
gate 1 "frontmatter has name + description" test $? -eq 0

ls "$DIR"/scripts/* >/dev/null 2>&1
gate 2 "deterministic core present (scripts/ non-empty)" test $? -eq 0

! grep -rqiE '<script[^>]+src="https?://' "$DIR/scripts" "$DIR/SKILL.md"
gate 3 "no remote CDN scripts" test $? -eq 0

n=$(find "$DIR/samples" -type f | wc -l | tr -d ' ')
test "$n" -ge 3
gate 4 "samples >= 3 files (found $n)" test $? -eq 0

lines=$(wc -l < "$DIR/SKILL.md" | tr -d ' ')
test "$lines" -le 200
gate 5 "SKILL.md <= 200 lines ($lines)" test $? -eq 0

! grep -qiE '\b(leverage|utilize|delve|seamless(ly)?|unlock the power)\b' "$DIR/SKILL.md"
gate 6 "no slop vocabulary in SKILL.md" test $? -eq 0

grep -qi 'failure mode' "$DIR/SKILL.md"
gate 7 "failure modes documented" test $? -eq 0

if [ "$fail" -eq 0 ]; then echo "OK: $NAME passes all mechanical gates."; else exit 1; fi
