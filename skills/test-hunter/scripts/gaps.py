#!/usr/bin/env python3
"""Coverage gap hunter: join coverage data with git churn to rank which
uncovered files need tests first.

Supports lcov text format (SF:/DA:/end_of_record) and coverage.py JSON.
Risk = churn_weight * (1 - coverage). Churn = commit count per file since
--churn-since. Deterministic.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys


def fail(msg):
    print(f"gaps error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_lcov(path):
    files = {}
    cur, total, hit = None, 0, 0
    for line in open(path):
        line = line.strip()
        if line.startswith("SF:"):
            cur, total, hit = line[3:], 0, 0
        elif line.startswith("DA:"):
            parts = line[3:].split(",")
            total += 1
            if len(parts) > 1 and int(parts[1]) > 0:
                hit += 1
        elif line == "end_of_record" and cur:
            files[cur] = (total, hit)
            cur = None
    return files


def parse_coverage_json(path):
    data = json.load(open(path))
    files = data.get("files", {})
    out = {}
    for f, info in files.items():
        s = info.get("summary", {})
        out[f] = (max(1, s.get("num_statements", 1)),
                  round(s.get("covered_lines", 0)))
    return out


def git_churn(repo, since_days):
    cutoff = (dt.datetime.now() - dt.timedelta(days=since_days)).strftime("%Y-%m-%d")
    try:
        out = subprocess.run(
            ["git", "-C", repo, "log", f"--since={cutoff}",
             "--name-only", "--pretty=format:"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        fail("not a git repository or no history")
    churn = {}
    for line in out.splitlines():
        line = line.strip()
        if line:
            churn[line] = churn.get(line, 0) + 1
    return churn


def main():
    ap = argparse.ArgumentParser(prog="hunt.py gaps")
    ap.add_argument("repo")
    ap.add_argument("--coverage", required=True,
                    help="lcov (.info/.lcov) or coverage.py JSON file")
    ap.add_argument("--churn-since", type=int, default=90,
                    help="days of git history to count churn over")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--out", default="gaps.json")
    args = ap.parse_args()

    head = open(args.coverage, "r", errors="ignore").readline()
    if head.startswith("SF:"):
        cov = {f: {"statements": t, "covered": h}
               for f, (t, h) in parse_lcov(args.coverage).items()}
        fmt = "lcov"
    elif head.strip().startswith("{") and '"files"' in open(args.coverage).read(2000):
        cov = {f: {"statements": t, "covered": h}
               for f, (t, h) in parse_coverage_json(args.coverage).items()}
        fmt = "coverage-py-json"
    else:
        fail("unsupported coverage format; supported: lcov text "
             "(SF:/DA: lines) and coverage.py JSON")

    churn = git_churn(args.repo, args.churn_since)

    rows = []
    for path, c in cov.items():
        stmts, covered = c["statements"], c["covered"]
        if not stmts:
            continue
        coverage_pct = covered / stmts
        ch = 0
        for cand in (path, path.lstrip("./"), path.split("/")[-1]):
            if cand in churn:
                ch = churn[cand]
                break
        risk = round((ch + 1) * (1.0 - coverage_pct), 2)
        rows.append({"file": path, "coverage": round(coverage_pct, 3),
                     "statements": stmts, "churn_commits": ch, "risk": risk})

    rows.sort(key=lambda r: (-r["risk"], r["coverage"]))
    out = {
        "format": fmt,
        "churn_since_days": args.churn_since,
        "files_measured": len(rows),
        "fully_covered": sum(1 for r in rows if r["coverage"] >= 0.999),
        "zero_coverage": sum(1 for r in rows if r["coverage"] == 0),
        "top_gaps": rows[:args.top],
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"format={fmt} files={out['files_measured']} "
          f"zero_cov={out['zero_coverage']}")
    for r in out["top_gaps"][:5]:
        print(f"  risk={r['risk']:>7}  cov={int(r['coverage']*100):>3}%  "
              f"churn={r['churn_commits']:>3}  {r['file']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
