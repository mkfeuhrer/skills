# Samples

- `fixture-report.html` — grade card produced from `tests/fixtures`, a small
  pytest project with planted issues (flaky test, over-mocked test,
  assertion-less test, uncovered function). Demonstrates all four detectors.
  Run `python3 scripts/hunt.py static tests/fixtures --out s.json` etc. to
  reproduce.
