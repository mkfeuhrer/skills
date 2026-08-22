# Rewrite Rules (agent-edited, applies after scan.py)

scan.py measures. The agent edits. Rules keep cuts meaning-preserving:

1. **Hedge preambles** — delete "It's worth noting that", "generally speaking",
   "in many cases" outright. Say the thing directly.
2. **Filler transitions** — replace sentence-start "Moreover, / Additionally, /
   Furthermore," with a real connective or nothing. They add words, not meaning.
3. **"Not just X but Y"** — allowed once per piece. Rewrite others as plain
   contrast or drop.
4. **Tricolons** — keep only if the parallelism earns it. Otherwise break into
   two clauses or vary length.
5. **Slop vocabulary** — swap per occurrence:
   leverage→use, utilize→use, delve→look/read, seamless→smooth, robust→solid,
   vibrant→lively, unlock→open, journey→path, cutting-edge→new,
   transformative→changing, supercharge→speed up, elevate→raise,
   empower→let/enable.
6. **Adjective stacking** — keep one adjective, cut the rest.
7. **Boilerplate closers / generic openers** — delete; start/end on the actual
   point.
8. **Cadence** — after cuts, re-read aloud. If every sentence is the same
   length, deliberately split or merge one.

Never change a fact, claim, number, name, or link. Cutting is cosmetic.
Re-run scan.py on the cleaned text; the index should drop. If it does not,
report both numbers honestly.
