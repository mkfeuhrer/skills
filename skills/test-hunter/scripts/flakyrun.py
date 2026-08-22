#!/usr/bin/env python3
"""Flaky test hunter: run a JUnit-XML-emitting command N times, aggregate
per-test outcomes across runs.

Runner-agnostic by design: anything that can emit JUnit XML works
(pytest --junitxml=..., jest --reporters=jest-junit, go via gotestsum,
Gradle/JUnit/.NET natively). We never read the source; only results.
"""
import argparse
import json
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET


def fail(msg):
    print(f"flakyrun error: {msg}", file=sys.stderr)
    sys.exit(1)


def run_once(cmd, junit_path, timeout):
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout)
    try:
        tree = ET.parse(junit_path)
    except (OSError, ET.ParseError) as e:
        fail(f"run did not produce readable JUnit XML at {junit_path}: {e}")
    root = tree.getroot()
    results = {}
    for tc in root.iter("testcase"):
        key = f"{tc.get('classname', '')}::{tc.get('name', '?')}"
        if tc.find("failure") is not None or tc.find("error") is not None:
            status = "fail"
        elif tc.find("skipped") is not None:
            status = "skip"
        else:
            status = "pass"
        msg = ""
        if status != "pass":
            node = tc.find("failure") if tc.find("failure") is not None else \
                (tc.find("error") or tc.find("skipped"))
            msg = (node.get("message", "") or "")[:200]
        results[key] = {"status": status, "msg": msg}
    return proc.returncode, results


def main():
    ap = argparse.ArgumentParser(prog="hunt.py flaky")
    ap.add_argument("cmd", help="test command that emits JUnit XML")
    ap.add_argument("--junit", required=True,
                    help="fixed path where the command writes JUnit XML")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=1800,
                    help="per-run timeout seconds")
    ap.add_argument("--out", default="flaky.json")
    args = ap.parse_args()
    if args.runs < 2:
        fail("need at least 2 runs to detect flakiness")

    history = {}   # key -> list of statuses
    last_msgs = {}
    for i in range(args.runs):
        code, results = run_once(args.cmd, args.junit, args.timeout)
        for key, r in results.items():
            history.setdefault(key, []).append(r["status"])
            if r["status"] == "fail":
                last_msgs[key] = r["msg"]
        print(f"run {i+1}/{args.runs}: rc={code} "
              f"tests={len(results)} "
              f"failing={sum(1 for r in results.values() if r['status']=='fail')}")

    tests = []
    for key, statuses in sorted(history.items()):
        passes = sum(1 for s in statuses if s == "pass")
        fails = sum(1 for s in statuses if s == "fail")
        skips = sum(1 for s in statuses if s == "skip")
        tests.append({
            "test": key,
            "runs": len(statuses),
            "passes": passes,
            "fails": fails,
            "skips": skips,
            "pass_rate": round(passes / len(statuses), 3),
            "last_error": last_msgs.get(key, ""),
        })

    measured = [t for t in tests if t["runs"] and t["skips"] < t["runs"]]
    flaky = [t for t in measured if 0 < t["passes"] < t["passes"] + t["fails"]]
    always_failing = [t for t in measured if t["passes"] == 0]
    stable = [t for t in measured if t["fails"] == 0]

    reliability = round(
        statistics.mean(t["pass_rate"] for t in measured), 3
    ) if measured else 1.0

    out = {
        "command": args.cmd,
        "junit": args.junit,
        "total_runs": args.runs,
        "tests_measured": len(measured),
        "stable": len(stable),
        "flaky": sorted(flaky, key=lambda t: t["pass_rate"]),
        "always_failing": always_failing,
        "reliability": reliability,
        "note": "retries mask coupling - a flaky test fixed by retrying is "
                "not fixed (see references/narrative.md)",
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"measured={len(measured)} stable={len(stable)} "
          f"flaky={len(flaky)} always_failing={len(always_failing)} "
          f"reliability={reliability}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
