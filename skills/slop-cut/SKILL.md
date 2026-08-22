---
name: slop-cut
description: Measure how AI-sounding a piece of writing is and cut the slop. Scans READMEs, blog drafts, PR descriptions, and docs for slop signals (hedging, tricolons, slop vocabulary, cadence uniformity) and produces a numeric Slop Index plus a before/after cleaned version. Use when asked to "check my writing for AI slop", "deslop this", "is this text too AI-sounding", "tighten this README", or before publishing anything. Self-contained auditor, not a style prompt.
---

# Slop Cut

An auditor that MEASURES AI-sounding text instead of just prompting against it.
Every public skill in this repo passes through it before shipping
(CHECKLIST.md gate 7 points here).

## Why this exists

"Deslop" skills are style prompts — they nudge, they don't measure. Slop Cut
renders a scorecard so you can see whether the cut worked, and so readers trust
the number.

## When to use

- "Is this too AI-sounding?" / "check my writing for AI slop"
- "Deslop this README / blog draft / PR description"
- Pre-publish pass on any artifact.

## How to run

Zero-dependency Python 3 (stdlib only).

### 1. Scan
```bash
python3 scripts/scan.py path/to/text.md --out signals.json
```
Outputs `slop_index` (0-100) and per-category signals with snippets.

### 2. Read signals, then cut
Read `references/rewrite.md`. Apply the rules to produce `cleaned.md`.
Never change facts, numbers, names, or links.

### 3. Re-scan the cleaned version
```bash
python3 scripts/scan.py cleaned.md --out signals2.json
```
Report both indices (before -> after).

### 4. Render the diff card (optional)
```bash
python3 scripts/report.py signals.json --original text.md \
    --cleaned cleaned.md --out slop-report.html
```

## Signal weights (sum 100)

| Category | Weight | What it catches |
|---|---|---|
| Rhythm | 35 | low burstiness (stdev of sentence length), 17-23 word uniform band, consecutive same-band |
| Structure | 25 | "not just X but Y", tricolons, boilerplate closers, generic openers |
| Vocabulary | 20 | slop word list, 3+ stacked adjectives before a noun |
| Hedging | 12 | hedge preambles, filler transitions at sentence start |
| Punctuation | 8 | em-dash density (weak, by design), no semicolons in long text |

## Agent role (narrow)

Run scan.py, read the top signals, cut per rewrite.md, re-scan, render. Do NOT
invent a lower score — if the index does not drop, say so.

## Failure modes

- Very short input (<40 words): rhythm signals disabled; structure/vocabulary
  still fire and are reported.
- English-tuned; non-English input is out of scope — state it.

## Cross-check

Run an output through `test-hunter`? No — run published artifacts through
`slop-cut` before posting.
