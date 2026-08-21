---
name: git-story
description: Turn any git repository's history into an animated HTML story - eras, key commits, growth curves, and dramatic moments. Trigger when the user asks to "tell this repo's story", "visualize git history", "make a timeline of this project", "git-story", "repo history video", or "how did this project evolve".
---

# git-story

Produce `git-story.html`: a self-contained animated timeline of how a git
repository came to be. The output must open offline and look good as a static
screenshot (poster frame).

## Workflow

1. Confirm the target repo path with the user. Default: current directory.
2. Run extraction:
   `python3 <skill-dir>/scripts/extract.py <repo-path> --out story.json`
   It prints a compact digest. Read it.
3. Write the narrative: edit `story.json` fields per `references/narrative.md`
   - `meta.title`, `meta.tagline` (poster headline)
   - each era's `title` and `caption`
   - each highlight gets a plain-English `note` (one sentence)
   Do not change any numeric fields.
4. Render:
   `python3 <skill-dir>/scripts/generate.py story.json git-story.html`
5. Verify: file exists, size > 20KB, valid JSON went in. Report the absolute
   path and offer to screenshot it (`scripts/screenshot.sh` from repo root).

Never hand-edit the HTML. All facts come from extract.py; only narrative
strings are yours.

## Failure modes

- Empty repo / 0 commits: extraction exits 1 with message; tell the user.
- Single-commit repo: still works; one era titled "Day Zero" style.
- Huge repos (>200k commits): extract.py samples automatically; expect slower
  runs. Warn the user it may take a minute.
- Detached HEAD or bare repo without HEAD: exits with clear error.
