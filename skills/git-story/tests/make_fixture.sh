#!/usr/bin/env bash
# Build a deterministic fixture repo for testing git-story end to end.
# Usage: tests/make_fixture.sh [dest-dir]
set -euo pipefail
DEST="${1:-$(mktemp -d)/fixture-repo}"
mkdir -p "$DEST" && cd "$DEST"
git init -q
git config user.email t@t.co && git config user.name Tester

commit() { echo "$2" > "$1"; git add .; GIT_AUTHOR_DATE="$3" GIT_COMMITTER_DATE="$3" git commit -qm "$4"; }

# era 1: bootstrap (Jan-Mar 2024)
for i in 1 2 3 4 5; do
  commit "app.py" "print($i)" "2024-01-0${i}T10:00:00" "initial setup $i"
done
# era 2: growth (Jun-Aug 2024) — big gap triggers new era
for i in 1 2 3; do
  commit "app.py" "$(printf "wave $i line\n%.0s" {1..300})" "2024-06-1${i}T10:00:00" "feature wave $i"
done
# era 3: the deletion (2025)
commit "app.py" "# minimal now" "2025-02-01T10:00:00" "massive cleanup"

echo "$DEST"
