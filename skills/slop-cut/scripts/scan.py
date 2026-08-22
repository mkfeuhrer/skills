#!/usr/bin/env python3
"""Slop Cut scanner: measure AI-sounding text instead of just prompting against
it. Emits a signals.json + numeric Slop Index. Deterministic, stdlib only.

Signal weights sum to 100. Em-dash is deliberately a weak signal (trivially
suppressed); rhythm uniformity and hedge preambles carry most of the weight,
per published research on what actually moves detectors.

Categories:
  Rhythm (35)      sentence-length stdev, % sentences in 17-23 word band,
                   % consecutive same-band sentences
  Structure (25)   "not just X but Y", tidy tricolons, boilerplate closers,
                   generic openings
  Vocabulary (20)  slop word list, adjective stacking (3+ adj before noun)
  Hedging (12)    hedge preambles, filler transitions at sentence start
  Punctuation (8) em-dash density (weak), semicolon absence in long text
"""
import argparse
import json
import math
import re
import sys

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[A-Za-z']+")

# Structure
NOT_JUST = re.compile(r"not just\b.*?\bbut\b", re.I)
TRICOLON = re.compile(r"([^,]*,){2,}\s*\w+\s+and\b")
CLOSERS = [
    r"as (ai|technology) continues to evolve",
    r"in (conclusion|summary)",
    r"the future (of|is)",
    r"stay tuned",
    r"it's (important|worth noting) to (remember|note)",
]
OPENERS = [
    r"in today's (fast-paced|rapidly (changing|evolving))",
    r"in the (world|realm) of",
    r"the (modern|digital) (world|age|era)",
]
# Vocabulary
SLOP_WORDS = [
    "leverage", "utilize", "utilise", "delve", "seamless", "seamlessly",
    "robust", "vibrant", "unlock", "journey", "game-changer", "game changer",
    "cutting-edge", "cutting edge", "revolutionary", "transformative",
    "holistic", "synergy", "supercharge", "elevate", "empower", "frictionless",
    "best-in-class", "world-class", "navigate the", "unlock the power",
    "harness the", "in the realm of", "it's worth noting", "dive in", "dive into",
    "at the end of the day", "when it comes to", "a testament to",
]
ADJ_STACK = re.compile(
    r"\b(" + "|".join([
        "beautiful", "stunning", "amazing", "incredible", "powerful",
        "simple", "clean", "modern", "elegant", "intuitive", "seamless",
        "robust", "vibrant", "minimal", "sleek", "dynamic",
    ]) + r")(\s+" + r"\b(" + "|".join([
        "beautiful", "stunning", "amazing", "incredible", "powerful",
        "simple", "clean", "modern", "elegant", "intuitive", "seamless",
        "robust", "vibrant", "minimal", "sleek", "dynamic",
    ]) + r")){2,}")
# Hedging
HEDGE_PREAMBLE = re.compile(
    r"^(it's (important|worth noting|worth mentioning)|generally speaking|"
    r"in many cases|it should be noted|needless to say|to be honest|"
    r"frankly speaking)", re.I)
FILLER_TRANSITION = re.compile(
    r"^(moreover|additionally|furthermore|that said|that being said|"
    r"overall|in essence|essentially|notably|importantly),", re.I)
EM_DASH = re.compile(r"—|–")
SEMICOLON = re.compile(r";")


def sentences(text):
    parts = SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def words(s):
    return WORD.findall(s.lower())


def stdev(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def main():
    ap = argparse.ArgumentParser(prog="scan.py")
    ap.add_argument("text", help="path to .md/.txt, or '-' for stdin")
    ap.add_argument("--out", default="signals.json")
    args = ap.parse_args()

    if args.text == "-":
        text = sys.stdin.read()
    else:
        text = open(args.text, errors="ignore").read()

    sents = sentences(text)
    n = len(sents)
    lengths = [len(words(s)) for s in sents]
    signals = []
    contrib = {"rhythm": 0.0, "structure": 0.0, "vocabulary": 0.0,
               "hedging": 0.0, "punctuation": 0.0}

    def add(cat, sid, strength, snippet, weight):
        signals.append({"category": cat, "id": sid,
                         "strength": round(clamp(strength), 3),
                         "snippet": snippet[:160]})
        contrib[cat] += strength * weight

    # --- Rhythm (35) ---
    sd = stdev(lengths)
    sd_strength = clamp(sd / 6.0)            # very low variance = robotic
    if n >= 4:
        add("rhythm", "low_burstiness", sd_strength,
            f"stddev sentence length = {sd:.1f} words", 15)
    band = [1 if (17 <= l <= 23) else 0 for l in lengths]
    band_pct = sum(band) / n if n else 0
    if n >= 4:
        add("rhythm", "uniform_band", band_pct,
            f"{int(band_pct*100)}% of sentences fall in the 17-23 word band", 12)
    same = 0
    for i in range(1, n):
        if (17 <= lengths[i] <= 23) and (17 <= lengths[i-1] <= 23):
            same += 1
    if n >= 4:
        add("rhythm", "consecutive_band", same / max(n - 1, 1),
            f"{same} consecutive 17-23 word sentences", 8)

    # --- Structure (25) ---
    if NOT_JUST.search(text):
        add("structure", "not_just_but", 1.0,
            NOT_JUST.search(text).group(0)[:120], 10)
    if TRICOLON.search(text):
        add("structure", "tricolon", 0.8,
            TRICOLON.search(text).group(0)[:120], 6)
    for pat in CLOSERS:
        m = re.search(pat, text, re.I)
        if m:
            add("structure", "boilerplate_closer", 1.0, m.group(0)[:120], 5)
            break
    for pat in OPENERS:
        m = re.search(pat, text, re.I)
        if m:
            add("structure", "generic_opener", 1.0, m.group(0)[:120], 4)
            break

    # --- Vocabulary (20) ---
    low = text.lower()
    hits = []
    for w in SLOP_WORDS:
        c = low.count(w)
        if c:
            hits.append((w, c))
    slop_count = sum(c for _, c in hits)
    if hits:
        add("vocabulary", "slop_words", clamp(slop_count / 8.0),
            ", ".join(f"{w}x{c}" for w, c in hits[:8]), 14)
    stack = ADJ_STACK.search(text)
    if stack:
        add("vocabulary", "adjective_stack", 1.0, stack.group(0)[:120], 6)

    # --- Hedging (12) ---
    hpre = [s for s in sents if HEDGE_PREAMBLE.match(s)]
    if hpre:
        add("hedging", "hedge_preamble", clamp(len(hpre) / 3.0),
            hpre[0][:120], 7)
    ftr = [s for s in sents if FILLER_TRANSITION.match(s)]
    if ftr:
        add("hedging", "filler_transition", clamp(len(ftr) / 3.0),
            ftr[0][:120], 5)

    # --- Punctuation (8) ---
    total_words = sum(lengths)
    em = len(EM_DASH.findall(text))
    em_density = em / max(total_words, 1) * 100
    add("punctuation", "em_dash", clamp(em_density / 1.5),
        f"{em} em-dashes per {total_words} words (weak signal)", 5)
    if total_words > 120 and not SEMICOLON.search(text):
        add("punctuation", "no_semicolons", 0.6,
            "long text with zero semicolons (monotone cadence)", 3)

    index = round(min(sum(contrib.values()), 100.0), 1)
    out = {
        "sentences": n,
        "words": total_words,
        "slop_index": index,
        "contributions": {k: round(v, 2) for k, v in contrib.items()},
        "signals": sorted(signals, key=lambda s: -s["strength"]),
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"sentences={n} words={total_words} slop_index={index}")
    print("by category:", ", ".join(f"{k}={v:.1f}" for k, v in contrib.items()))
    for s in out["signals"][:6]:
        print(f"  [{s['category']}] {s['id']} ({s['strength']}) {s['snippet'][:70]}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
