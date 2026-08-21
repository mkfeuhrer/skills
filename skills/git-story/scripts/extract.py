#!/usr/bin/env python3
"""Extract a git repo's history into story.json for git-story.

Deterministic: same repo + same args -> same output (except generated_at).
Handles huge repos by capping the parsed log and sampling growth points.
"""
import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys

MAX_LOG_COMMITS = 50000      # cap metadata parsing for gigantic repos
GROWTH_POINTS = 300          # sampled points on the growth curve
HIGHLIGHTS_PER_ERA = 3
ERA_MIN_COMMITS = 8
MAX_ERAS = 12


def run(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True,
                          text=True, check=True).stdout


def fail(msg):
    print(f"git-story extract error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_log(repo):
    """One pass over the log with shortstat per commit."""
    fmt = "C|%H|%at|%an|%s"
    out = run(repo, ["log", "--no-merges", "--date-order",
                     f"--pretty=format:{fmt}", "--shortstat"])
    commits = []
    cur = None
    for line in out.splitlines():
        if not line.strip():
            continue
        if line.startswith("C|"):
            if cur:
                commits.append(cur)
            _, sha, at, author, subject = line.split("|", 4)
            cur = {"sha": sha, "ts": int(at), "author": author,
                   "subject": subject, "ins": 0, "del": 0}
        else:
            parts = line.split(",")
            for p in parts:
                p = p.strip()
                if "insertion" in p:
                    cur["ins"] = int(p.split()[0])
                elif "deletion" in p:
                    cur["del"] = int(p.split()[0])
    if cur:
        commits.append(cur)
    return commits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="story.json")
    args = ap.parse_args()

    try:
        count = int(run(args.repo, ["rev-list", "--count", "HEAD"]).strip())
    except subprocess.CalledProcessError:
        fail("not a git repository or no HEAD commits")

    total_commits = count
    commits = parse_log(args.repo)
    if not commits:
        fail("repository has no non-merge commits")
    sampled_log = len(commits) > MAX_LOG_COMMITS
    stride = max(1, len(commits) // MAX_LOG_COMMITS) if sampled_log else 1

    # log is newest-first and not timestamp-monotonic (rebases, clock skew);
    # normalize to oldest-first sorted by time
    commits = list(reversed(commits[::stride]))
    commits.sort(key=lambda c: (c["ts"], c["sha"]))
    n = len(commits)

    first, last = commits[0], commits[-1]
    span_days = max(1, round((last["ts"] - first["ts"]) / 86400))

    contributors = {}
    for c in commits:
        contributors[c["author"]] = contributors.get(c["author"], 0) + 1
    top_contributors = sorted(contributors.items(), key=lambda x: -x[1])[:10]

    # growth curve: cumulative churn sampled to GROWTH_POINTS
    growth = []
    cum = 0
    step = max(1, n // GROWTH_POINTS)
    for i, c in enumerate(commits):
        cum += c["ins"] + c["del"]
        if i % step == 0 or i == n - 1:
            growth.append({"ts": c["ts"], "churn": cum})

    # eras: split at large time gaps, widening the threshold until the story
    # fits in MAX_ERAS chapters
    gaps = [commits[i + 1]["ts"] - commits[i]["ts"] for i in range(n - 1)]
    median_gap = statistics.median(gaps) if gaps else 0

    def segment(threshold):
        spans = []
        start = 0
        for i in range(n - 1):
            if gaps[i] > threshold and i - start + 1 >= ERA_MIN_COMMITS:
                spans.append((start, i))
                start = i + 1
        spans.append((start, n - 1))
        # fold a trailing sliver into the previous era
        if len(spans) > 1 and spans[-1][1] - spans[-1][0] + 1 < ERA_MIN_COMMITS:
            prev = spans[-2]
            spans[-2:] = [(prev[0], spans[-1][1])]
        return spans

    factor = 8
    eras = segment(max(90 * 86400, factor * median_gap)) if median_gap else \
        [(0, n - 1)]
    while len(eras) > MAX_ERAS:
        factor *= 4
        eras = segment(max(90 * 86400, factor * median_gap))

    # Fallback: actively-maintained repos never go silent long enough to split
    # on gaps. Give any multi-year history chapter boundaries so the story
    # does not collapse into one era. Deterministic: equal-commit thirds.
    if len(eras) == 1 and n >= 60 and span_days > 730:
        cuts = [n * i // 3 for i in (1, 2)]
        eras = [(0, cuts[0] - 1), (cuts[0], cuts[1] - 1), (cuts[1], n - 1)]

    era_objs = []
    for idx, (s, e) in enumerate(eras):
        seg = commits[s:e + 1]
        ins = sum(c["ins"] for c in seg)
        dele = sum(c["del"] for c in seg)
        highlights = sorted(seg, key=lambda c: -(c["ins"] + c["del"]))[:HIGHLIGHTS_PER_ERA]
        era_objs.append({
            "index": idx,
            "start_ts": seg[0]["ts"], "end_ts": seg[-1]["ts"],
            "commit_count": len(seg),
            "insertions": ins, "deletions": dele,
            "title": "", "caption": "",
            "highlights": [{"sha": h["sha"], "ts": h["ts"],
                            "author": h["author"], "subject": h["subject"],
                            "ins": h["ins"], "del": h["del"], "note": ""}
                           for h in highlights],
        })

    biggest = max(commits, key=lambda c: c["ins"] + c["del"])
    mass_del = min(commits, key=lambda c: c["ins"] - c["del"])
    stall = None
    if gaps:
        gi = max(range(len(gaps)), key=lambda i: gaps[i])
        stall = {"after_sha": commits[gi]["sha"],
                 "days": round(gaps[gi] / 86400),
                 "resumed_ts": commits[gi + 1]["ts"]}

    story = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "meta": {"repo_path": args.repo, "title": "", "tagline": ""},
        "stats": {
            "total_commits": total_commits,
            "sampled": sampled_log,
            "contributors": len(contributors),
            "span_days": span_days,
            "first_commit_ts": first["ts"],
            "last_commit_ts": last["ts"],
            "total_insertions": sum(c["ins"] for c in commits),
            "total_deletions": sum(c["del"] for c in commits),
        },
        "top_contributors": [{"name": k, "commits": v} for k, v in top_contributors],
        "growth": growth,
        "eras": era_objs,
        "drama": {
            "biggest_commit": {"sha": biggest["sha"], "ts": biggest["ts"],
                               "subject": biggest["subject"],
                               "ins": biggest["ins"], "del": biggest["del"], "note": ""},
            "mass_deletion": {"sha": mass_del["sha"], "ts": mass_del["ts"],
                              "subject": mass_del["subject"],
                              "ins": mass_del["ins"], "del": mass_del["del"], "note": ""}
            if mass_del["del"] > 100 else None,
            "longest_stall": stall,
        },
    }

    with open(args.out, "w") as f:
        json.dump(story, f, indent=1)

    print(f"repo={args.repo} commits={total_commits} eras={len(era_objs)} "
          f"contributor_count={len(contributors)} span_days={span_days}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
