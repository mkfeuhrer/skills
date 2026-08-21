# Skill Quality Checklist

A skill ships only when every gate below passes. Gates are ordered; stop at the
first failure and fix it. `scripts/validate.sh <skill>` checks the mechanical
gates (marked [M]); judgment gates are human/agent-reviewed.

1. **[M] Trigger test** — SKILL.md `description` contains concrete trigger
   phrases. Test: 3 phrasings a user would say activate it; 3 near-miss
   phrasings ("show me git log") do NOT.
2. **[M] Deterministic core** — All parsing/computation lives in `scripts/`.
   The agent never hand-writes generated output; it only supplies narrative
   JSON per `references/*.md`.
3. **[M] Zero-dependency run** — Generated artifacts open offline. No CDN
   `<script src="http...">`. Vendored libs only if unavoidable.
4. **[M] Sample proof** — `samples/` has >=3 pre-generated outputs, including
   one adversarial input (empty / single-commit / huge repo).
5. **Failure modes documented** — README or SKILL.md states what happens on
   empty, huge, and malformed inputs.
6. **Cross-agent check** — Ran end-to-end on Claude Code AND OpenCode.
7. **[M] No slop** — SKILL.md <= 200 lines; no filler adjectives, no
   "leverage/utilize/delve"; passes ai-slop review.
8. **Demo asset** — Screenshot/GIF in samples/, blog.md drafted.
