#!/usr/bin/env bash
# Scaffold a new skill folder. Usage: scripts/scaffold.sh <skill-name> "<one-line description>"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: scaffold.sh <skill-name> \"<description>\"}"
DESC="${2:?usage: scaffold.sh <skill-name> \"<description>\"}"
DIR="$ROOT/skills/$NAME"
mkdir -p "$DIR"/{scripts,references,tests,samples}

cat > "$DIR/SKILL.md" <<EOF
---
name: $NAME
description: $DESC. Trigger with phrases like "$NAME", plus 2 more concrete triggers here.
---

# $NAME

One paragraph: what this does and what artifact it produces.

## Workflow

1. Gather input from the user (state exactly what you need).
2. Run \`python3 scripts/extract.py <input> > story.json\`.
3. Edit story.json narrative fields per \`references/narrative.md\`.
4. Run \`python3 scripts/generate.py story.json <output>.html\`.
5. Open/verify the artifact; report the output path.

## Failure modes

- Empty input: what happens.
- Huge input: what happens.
EOF

touch "$DIR/references/narrative.md" "$DIR/blog.md"
echo "Scaffolded $DIR — fill in SKILL.md workflow and narrative.md before validating."
