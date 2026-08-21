# I turned git history into an animated story — with one agent skill

Every repo has a story: the bootstrap, the rewrite, the quiet years, the
revival. But `git log` is a wall of text, and nobody shares a wall of text.

So I built **git-story** — a single agent skill that turns any repository into
a self-contained, animated HTML page. Point your coding agent at a repo and ask
for its story.

## How it works

The design rule that matters: **the deterministic work lives in scripts, not
prompts.**

1. `extract.py` does one pass over `git log --shortstat`, sorts commits by time
   (yes, `--date-order` lies — rebases and clock skew break naive ordering),
   buckets the timeline into eras at large gaps, finds the biggest commit, the
   mass deletion, and the longest silence.
2. The agent's only job is narrative: naming eras ("The Rewrite", "Maintenance
   Mode") and writing one-sentence notes per key commit.
3. `generate.py` renders everything to a single offline HTML file. Inline SVG,
   no CDN, no dependencies. The poster frame at the top is designed to be
   screenshot-first.

Because the heavy lifting is scripted, the output quality doesn't depend on how
good the model is at writing JavaScript that week. That's also what makes it
work across agents — same SKILL.md, same result in Claude Code or OpenCode.

## What I learned shipping it

- **Test on a huge real repo before you ship.** On express (6,158 commits) the
  first era detection produced 67 broken chapters — half of them ending before
  they started — because git's date-order isn't timestamp order. Sorting by
  time and adaptively widening the gap threshold fixed it.
- **Screenshot your own artifacts.** My first screenshot script passed a
  relative path into `file://`, so Chromium screenshotted about:blank and told
  me it was fine. Absolute paths only.
- **Ship samples with the skill.** Three pre-generated outputs, including one
  adversarial input, are worth more than any README promise.

## Try it

```shell
git clone https://github.com/mkfeuhrer/skills.git
cp -r skills/skills/git-story ~/.claude/skills/
```

Then, in any repo: "tell this repo's story."

Samples live in [`skills/git-story/samples/`](../skills/git-story/samples/) —
express (the flagship demo), my blog repo, and a single-commit adversarial
case.
