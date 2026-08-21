# Narrative Guide for git-story

You write only the story fields in story.json. Numbers are never yours to
change. Facts first, flavor second: a reader should learn something true.

## meta.title

Formula options (pick one, keep under 60 chars):
- "The Story of <repo>"
- "<N> commits, one idea: <what the project is>"
- "How <repo> became <what it is today>"

## meta.tagline

One sentence with at least two hard numbers, e.g.:
"2,847 commits from 112 contributors over 6 years."

## Era titles and captions

Read each era's date range, commit_count, insertions/deletions, and highlight
subjects. Then:

- Title: 2-4 words, evocative but honest. Patterns that work:
  - Origin eras: "The Bootstrap", "Day Zero", "First Blood"
  - Growth: "Finding Shape", "The API Hardens", "Going Public"
  - High churn + deletions: "The Rewrite", "Breaking Things"
  - Long low-activity era: "Maintenance Mode", "The Quiet Years"
- Caption: ONE sentence stating what happened and why it matters. Anchor to
  evidence in the highlights ("the router rewrite landed here"). No adjectives
  you cannot defend from the data.

## Highlight notes

For each highlight commit write one plain-English `note`: what this commit did
and why it was heavy or pivotal. Translate jargon: "refactor core" ->
"restructured the central module". If the subject is opaque, describe the
churn instead ("a 12,000-line overhaul touching the whole tree").

## Drama notes

- biggest_commit.note: name what changed, not just how big it is.
- mass_deletion.note: speculate sparingly; prefer "removed X lines of Y".
- Leave longest_stall as-is unless a note field exists.

## Tone rules

- Confident, concrete, zero filler ("journey", "testament to", "vibrant").
- Never invent causes for changes you cannot see.
- Short sentences. A story read in 60 seconds beats an essay.
