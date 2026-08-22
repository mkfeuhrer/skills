---
name: test-hunter
description: Audit a codebase's test suite for missing tests, critical coverage gaps, flaky tests, and over-mocked or fake tests. Produces a single A-F graded HTML report card with per-finding fix recommendations. Use when asked to "audit tests", "find flaky tests", "where are my test gaps", "review test quality", or before shipping to flag test-suite risk. Universal (works with pytest, jest, go, JUnit, Gradle via JUnit XML output).
---

# Test Hunter

One graded report card for everything wrong with a test suite: missing tests,
critical coverage gaps, flaky tests, and over-mocked or fake tests — each
finding paired with a concrete fix.

## Why this exists

Test-suite quality is invisible until it bites. This skill makes it visible and
graded, so "good enough" becomes a number.

## When to use

- "Audit my tests" / "how healthy is my test suite?"
- "Find flaky tests" / "why does CI pass locally but fail sometimes?"
- "Where should I add tests first?"
- Pre-shipping risk check on a repo.

## How to run (deterministic core)

Zero-dependency Python 3 (stdlib only). All heavy lifting is in scripts.

### 1. Static scan (always)
```bash
python3 scripts/hunt.py static <repo> --out static.json
```
Discovers test files, counts tests/skips, finds assertion-less tests and
over-mocked files (mock calls > assertions). Python + JS/TS.

### 2. Coverage gaps × churn (needs coverage data)
```bash
python3 scripts/gaps.py <repo> --coverage coverage.lcov --out gaps.json
# or coverage.py JSON:
python3 scripts/gaps.py <repo> --coverage coverage.json --out gaps.json
```
Parses lcov text or coverage.py JSON, joins with git churn (commits in last
90d), ranks files by `risk = churn * (1 - coverage)`.

### 3. Flaky hunter (opt-in, repeated runs)
```bash
python3 scripts/flakyrun.py "pytest --junitxml=report.xml" \
    --junit report.xml --runs 5 --out flaky.json
```
Your command must emit JUnit XML (pytest `--junitxml=`, jest `--reporters=jest-junit`, go via gotestsum, Gradle/JUnit/.NET natively). Runs N times, aggregates per-test pass rates.

### 4. Render the grade card
```bash
python3 scripts/generate.py static.json gaps.json flaky.json \
    --title "Acme API tests" --out report.html
```
Self-contained HTML (no CDN). If a section is omitted, that dimension shows
`–` (never guessed).

## Agent role (narrow)

After the scripts run, read `references/narrative.md` and write ≤120 words of
severity notes + one-line fixes, then re-run `generate.py --notes "..."`.
Do NOT run test suites yourself, do NOT invent numbers, do NOT auto-fix.

## Output

- `report.html` — shareable grade card (A–F per dimension + overall).
- Grade rules are deterministic and documented in `generate.py`.

## Failure modes

- No tests found → report says so, grade F, no shaming.
- Unsupported coverage format → clear error listing lcov / coverage.py JSON.
- Flaky skipped (`--runs 1` or absent) → section marked not measured, dash grade.

## Cross-check

Run any output back through `slop-cut` before posting publicly.
