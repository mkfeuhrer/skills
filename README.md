# mkfeuhrer/skills

Agent skills that produce shareable visual artifacts. Every skill ships
validated, with pre-generated samples — no vibes, no slop.

Works with Claude Code, OpenCode, Codex, and anything that reads the universal
`SKILL.md` format.

## Install

```shell
git clone https://github.com/mkfeuhrer/skills.git
cp -r skills/skills/<skill-name> ~/.claude/skills/
# or symlink for OpenCode: ln -s $PWD/skills/skills/<skill-name> ~/.config/opencode/skills/
```

## The gallery

| Skill | What it makes | Sample |
|-------|---------------|--------|
| [git-story](skills/git-story/) | Animated HTML timeline of how a repo came to be | [react sample](skills/git-story/samples/) |

## Quality promise

Every skill here passes all 8 gates in [CHECKLIST.md](CHECKLIST.md) before it
ships:

1. Trigger test (activates on intent, not on near-misses)
2. Deterministic core (scripts do the heavy lifting, agent does judgment)
3. Zero-dependency run (offline-safe, vendored libs only)
4. Sample proof (>=3 committed outputs incl. one adversarial input)
5. Failure modes documented
6. Cross-agent verified (Claude Code + OpenCode minimum)
7. No slop (<=200-line SKILL.md, passes ai-slop review)
8. Demo asset shipped (screenshot + blog post)

## License

MIT
