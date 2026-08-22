#!/usr/bin/env python3
"""Render test-hunter sections (static.json, flaky.json, gaps.json) into a
self-contained HTML grade card. No CDN, no external assets.
"""
import argparse
import json
import sys

GRADE_COLORS = {"A": "#3ddc84", "B": "#9bd64a", "C": "#f5c542",
                "D": "#f59042", "F": "#ff5d5d", "-": "#7a8290"}


def grade_letter(score, bands):
    """bands: list of (threshold, letter) ascending; returns letter when
    score <= threshold else last."""
    for thr, letter in bands:
        if score <= thr:
            return letter
    return bands[-1][1]


def compute_grades(static, flaky, gaps):
    g = {"mock_hygiene": "-", "hygiene": "-", "flakiness": "-", "gaps": "-",
         "overall": "-"}
    if static:
        tf = max(static.get("test_files", 0), 1)
        over = len(static.get("over_mocked_files", [])) / tf
        g["mock_hygiene"] = grade_letter(over, [(0.0, "A"), (0.05, "B"),
                                                (0.15, "C"), (0.30, "D"),
                                                (1.0, "F")])
        tests = max(static.get("tests", 0), 1)
        bad = (static.get("skips", 0) + static.get("assertion_less_total", 0)) / tests
        g["hygiene"] = grade_letter(bad, [(0.02, "A"), (0.05, "B"),
                                          (0.10, "C"), (0.20, "D"),
                                          (1.0, "F")])
    if flaky:
        rel = flaky.get("reliability", 1.0)
        g["flakiness"] = grade_letter(1 - rel, [(0.02, "A"), (0.05, "C"),
                                                (0.10, "D"), (1.0, "F")])
    if gaps:
        zero = gaps.get("zero_coverage", 0)
        top = (gaps.get("top_gaps") or [{"risk": 0}])[0]["risk"]
        score = top + zero * 0.5
        g["gaps"] = grade_letter(score, [(1.0, "A"), (3.0, "B"),
                                         (6.0, "C"), (10.0, "D"),
                                         (100.0, "F")])
    present = [v for v in g.values() if v != "-"]
    order = "FDCBA"
    if present:
        worst = min(present, key=lambda x: order.index(x))
        g["overall"] = worst
    return g


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def card(letter, label):
    return (f'<div class="dim"><div class="grade" style="color:'
            f'{GRADE_COLORS[letter]}">{letter}</div>'
            f'<div class="dimlabel">{label}</div></div>')


def main():
    ap = argparse.ArgumentParser(prog="generate.py")
    ap.add_argument("sections", nargs="+", help="static/flaky/gaps json files")
    ap.add_argument("--title", default="Test Suite Health")
    ap.add_argument("--out", default="report.html")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    static = flaky = gaps = None
    for p in args.sections:
        d = json.load(open(p))
        if "test_files" in d:
            static = d
        elif "reliability" in d or "flaky" in d:
            flaky = d
        elif "top_gaps" in d or "zero_coverage" in d:
            gaps = d

    grades = compute_grades(static, flaky, gaps)

    flaky_rows = ""
    if flaky:
        for t in flaky.get("flaky", [])[:8]:
            flaky_rows += (f'<li><b>{esc(t["test"])}</b> passed '
                           f'{t["passes"]}/{t["runs"]} '
                           f'({int(t["pass_rate"]*100)}%)</li>')
        for t in flaky.get("always_failing", [])[:5]:
            flaky_rows += f'<li class="bad"><b>{esc(t["test"])}</b> always fails</li>'
    gaps_rows = ""
    if gaps:
        for r in gaps.get("top_gaps", [])[:8]:
            gaps_rows += (f'<li><b>{esc(r["file"])}</b> {int(r["coverage"]*100)}% '
                          f'covered, {r["churn_commits"]} commits, risk {r["risk"]}</li>')
    over_rows = ""
    if static:
        for f in static.get("over_mocked_files", [])[:6]:
            over_rows += f"<li>{esc(f)}</li>"

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{esc(args.title)}</title><style>
body{{background:#0d1117;color:#e6edf3;font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:32px}}
h1{{margin:0 0 4px}} .sub{{color:#8b949e;margin-bottom:24px}}
.cards{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px}}
.dim{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px 20px;text-align:center}}
.grade{{font:700 38px/1 monospace}} .dimlabel{{color:#8b949e;font-size:12px;margin-top:6px}}
h2{{border-top:1px solid #30363d;padding-top:16px;margin-top:24px;font-size:16px}}
ul{{margin:8px 0;padding-left:20px}} li{{margin:3px 0}} .bad{{color:#ff8b8b}}
.notes{{background:#161b22;border-left:3px solid #3ddc84;padding:10px 14px;color:#c9d1d9}}
footer{{color:#6e7681;font-size:12px;margin-top:30px}}
</style></head><body>
<h1>{esc(args.title)}</h1>
<div class="sub">grades: A best &middot; F worst &middot; &ndash; not measured</div>
<div class="cards">
{card(grades['gaps'],'coverage gaps')}
{card(grades['flakiness'],'flakiness')}
{card(grades['mock_hygiene'],'mock hygiene')}
{card(grades['hygiene'],'suite hygiene')}
{card(grades['overall'],'overall')}
</div>
"""

    if flaky_rows:
        html += f"<h2>Flaky &amp; failing tests</h2><ul>{flaky_rows}</ul>"
    if gaps_rows:
        html += f"<h2>Top coverage gaps (by churn &times; missing coverage)</h2><ul>{gaps_rows}</ul>"
    if over_rows:
        html += f"<h2>Over-mocked test files</h2><ul>{over_rows}</ul>"

    if args.notes:
        html += f'<div class="notes"><b>Severity &amp; fixes:</b><br>{esc(args.notes)}</div>'

    html += (f'<footer>generated by test-hunter &middot; '
             f'deterministic grade thresholds in generate.py</footer></body></html>')

    open(args.out, "w").write(html)
    print(f"overall={grades['overall']} "
          f"gaps={grades['gaps']} flaky={grades['flakiness']} "
          f"mock={grades['mock_hygiene']} hygiene={grades['hygiene']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
