#!/usr/bin/env python3
"""Static test-suite scan: assertion-less tests, over-mocking, skips.

Language-agnostic by file extension; pattern sets for Python and JS/TS.
Deterministic: same repo tree -> same JSON.
"""
import argparse
import ast
import json
import os
import re
import sys

TEST_FILE_RE = re.compile(r"^(test_|.*_test\.|test\.py$|.*\.test\.|.*\.spec\.)")
JS_TEST_DEF = re.compile(r"^\s*(?:test|it)\s*\(\s*['\"`]")
PY_SKIP = re.compile(r"(pytest\.mark\.(skip|skipif|xfail)|@unittest\.skip)")
JS_SKIP = re.compile(r"\.\s*(skip|todo)\s*\(|\bxit\s*\(")
ASSERT_JS = re.compile(r"\bexpect\(")
MOCK_PY = re.compile(r"(mock\.patch|MagicMock|\bmonkeypatch|\bmocker\.\w+)", re.I)
MOCK_JS = re.compile(r"(jest\.mock|vi\.mock|\bmock[A-Z_(]|\bjest\.fn\b)", re.I)
ASSERT_LIKE = re.compile(r"pytest\.raises|assertRaises|assertWarns|assertLogs")


def is_test_file(path):
    return bool(TEST_FILE_RE.search(os.path.basename(path))) and path.suffix in (
        ".py", ".js", ".jsx", ".ts", ".tsx")


def scan_file(path):
    text = path.read_text(errors="ignore")
    lang = "python" if path.suffix == ".py" else "js"
    entry = {"file": str(path), "tests": 0, "skips": 0,
             "assertion_less": [], "assertions": 0, "mocks": 0,
             "over_mocked_funcs": []}

    if lang == "python":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return entry
        entry["skips"] = len(PY_SKIP.findall(text))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test"):
                entry["tests"] += 1
                seg = ast.get_source_segment(text, node) or ""
                asserts = sum(1 for n in ast.walk(node)
                              if isinstance(n, ast.Assert))
                mocks = len(MOCK_PY.findall(seg))
                entry["assertions"] += asserts
                entry["mocks"] += mocks
                if asserts == 0 and not ASSERT_LIKE.search(seg):
                    entry["assertion_less"].append(node.name)
                if mocks > asserts and asserts > 0:
                    entry["over_mocked_funcs"].append(node.name)
    else:
        matches = list(JS_TEST_DEF.finditer(text))
        entry["tests"] = len(matches)
        entry["skips"] = len(JS_SKIP.findall(text))
        for m in matches:
            start = text.find("\n", m.start())
            end = _matching_close_paren(text, m.end())
            body = text[start:end] if end > start else ""
            if not ASSERT_JS.search(body):
                name_m = re.match(r"[\"'`]([^\"'`]{1,60})", text[m.end():])
                entry["assertion_less"].append(name_m.group(1) if name_m else "?")
        entry["assertions"] = len(ASSERT_JS.findall(text))
        entry["mocks"] = len(MOCK_JS.findall(text))
    return entry


def _matching_close_paren(text, open_idx):
    depth = 0
    for i in range(open_idx, min(len(text), open_idx + 5000)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def main():
    ap = argparse.ArgumentParser(prog="hunt.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("static", help="scan test files for static issues")
    ps.add_argument("repo")
    ps.add_argument("--out", default="static.json")
    args = ap.parse_args()

    if args.cmd != "static":
        print(f"unknown subcommand {args.cmd}", file=sys.stderr)
        sys.exit(1)

    import pathlib
    files = []
    for root, dirs, names in os.walk(args.repo):
        dirs[:] = [d for d in dirs if d not in
                   ("node_modules", ".git", ".venv", "venv", "dist", "build")]
        for n in names:
            p = os.path.join(root, n)
            if is_test_file(pathlib.Path(p)):
                files.append(p)

    entries = []
    for f in sorted(files):
        try:
            entries.append(scan_file(pathlib.Path(f)))
        except OSError as e:
            print(f"warn: skipped {f}: {e}", file=sys.stderr)

    total_tests = sum(e["tests"] for e in entries)
    summary = {
        "repo": args.repo,
        "test_files": len(entries),
        "tests": total_tests,
        "skips": sum(e["skips"] for e in entries),
        "assertion_less_total": sum(len(e["assertion_less"]) for e in entries),
        "over_mocked_files": [
            e["file"] for e in entries if e.get("over_mocked_funcs")
        ],
        "files": entries,
    }
    with open(args.out, "w") as fh:
        json.dump(summary, fh, indent=1)
    print(f"files={summary['test_files']} tests={total_tests} "
          f"skips={summary['skips']} assertionless={summary['assertion_less_total']} "
          f"overmocked={len(summary['over_mocked_files'])}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
