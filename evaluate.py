"""Evaluation harness for MatrixMix.

Runs a fixed set of sample inputs through the real system and checks the results, then prints a report.
Exit code is 0 if every check passes, 1 otherwise, so it can be used in CI.

    python evaluate.py
"""
import sys
import time

from src.guardrails import clean_query, confidence, verify_results
from src.mood import recommend_by_mood
from src.similar import SongSimilarity

SONG_SEEDS = ["Starboy", "Heat Waves", "Blinding Lights", "Shape of You", "Bad Guy", "Sunflower"]

# (query, feature, comparison, threshold): the average of `feature` across the 10 results must satisfy it.
MOOD_CASES = [
    ("gym workout", "energy", ">", 0.75),
    ("party", "danceability", ">", 0.65),
    ("angry", "energy", ">", 0.75),
    ("sleep", "energy", "<", 0.35),
    ("chill", "energy", "<", 0.50),
    ("I want a chill song to play in a cafe", "acousticness", ">", 0.40),
    ("happy", "valence", ">", 0.60),
    ("sad rainy night", "valence", "<", 0.35),
]

# (input, what the guardrail should do)
BAD_INPUTS = [
    ("", "error"),
    ("     ", "error"),
    ("!!!???", "error"),
    ("chill\x00\x07 cafe", "clean"),
    ("a" * 500, "truncate"),
]

results = []  # (section, name, passed, detail)


def check(section, name, passed, detail=""):
    results.append((section, name, bool(passed), detail))


def evaluate_song_mode(model):
    for q in SONG_SEEDS:
        hits = model.search(q)
        if hits.empty:
            check("Song mode", f"find '{q}'", False, "song not found")
            continue
        idx = hits.index[0]
        seed = model.cat.loc[idx]
        recs = model.recommend(idx, k=10, clean_only=True)
        problems = verify_results(recs, k=10, seed_title=seed["title"])
        check("Song mode", f"'{q}': 10 results obey all rules",
              len(recs) == 10 and not problems, "; ".join(problems) or f"{len(recs)} results")
        seed_genres = set(seed["genres"])
        if seed_genres:
            share = sum(bool(seed_genres & set(g)) for g in recs["genres"]) / max(len(recs), 1)
            check("Song mode", f"'{q}': results share a genre with the seed", share >= 0.6, f"{share:.0%} share a genre")
        again = model.recommend(idx, k=10, clean_only=True)
        check("Song mode", f"'{q}': same answer on a second run", list(recs["title"]) == list(again["title"]))


def evaluate_mood_mode(model):
    for q, feat, op, threshold in MOOD_CASES:
        moods, recs = recommend_by_mood(model.cat, q, k=10, clean_only=True)
        if recs.empty:
            check("Mood mode", f"'{q}'", False, "no results")
            continue
        mean = recs[feat].mean()
        ok = mean > threshold if op == ">" else mean < threshold
        problems = verify_results(recs, k=10)
        check("Mood mode", f"'{q}': mean {feat} {op} {threshold}",
              ok and not problems and len(recs) == 10,
              f"moods={moods}, mean {feat}={mean:.2f}" + (f", problems: {problems}" if problems else ""))
        _, again = recommend_by_mood(model.cat, q, k=10, clean_only=True)
        check("Mood mode", f"'{q}': same answer on a second run", list(recs["title"]) == list(again["title"]))


def evaluate_guardrails(model):
    for raw, expected in BAD_INPUTS:
        qc = clean_query(raw)
        shown = repr(raw if len(raw) < 20 else raw[:10] + "..." + f"({len(raw)} chars)")
        if expected == "error":
            check("Guardrails", f"input {shown} is rejected", not qc.ok, qc.error or "was accepted")
        elif expected == "clean":
            check("Guardrails", f"input {shown} is cleaned", qc.ok and qc.text == "chill cafe", f"-> {qc.text!r}")
        elif expected == "truncate":
            check("Guardrails", f"input {shown} is truncated with a warning",
                  qc.ok and len(qc.text) <= 100 and bool(qc.warnings), f"-> {len(qc.text)} chars, warnings={len(qc.warnings)}")

    moods, recs = recommend_by_mood(model.cat, "xyz", k=10)
    check("Guardrails", "unrecognized mood returns nothing, not a guess", moods == [] and recs.empty)

    from src.mood import PROFILES
    leaked = []
    for mood in PROFILES:
        _, r = recommend_by_mood(model.cat, mood, k=10, clean_only=True)
        leaked += list(r[r["explicit"]]["title"])
    check("Guardrails", "'clean only' never returns an explicit song (all 14 moods)", not leaked, f"leaked: {leaked}" if leaked else "0 explicit songs")

    check("Guardrails", "self-check catches a bad list",
          bool(verify_results(_make_bad_list(model), k=10)), "duplicate + unsorted list was flagged")
    check("Guardrails", "low-confidence warning fires on weak matches",
          confidence(_make_weak_list(), "mood") is not None)


def _make_bad_list(model):
    row = model.cat.iloc[[0]].copy()
    bad = row.copy()
    bad = bad.loc[bad.index.repeat(3)].reset_index(drop=True)
    bad["score"] = [0.2, 0.9, 1.4]
    bad["why"] = ["a", "", "c"]
    return bad


def _make_weak_list():
    import pandas as pd
    return pd.DataFrame({"score": [0.5, 0.4, 0.3], "title": list("abc"), "artist": list("xyz"), "why": list("123")})


def main():
    start = time.time()
    print("Loading catalog...")
    model = SongSimilarity()
    print(f"Catalog: {len(model.cat):,} songs\n")

    evaluate_song_mode(model)
    evaluate_mood_mode(model)
    evaluate_guardrails(model)

    section = None
    for sec, name, passed, detail in results:
        if sec != section:
            print(f"\n== {sec} ==")
            section = sec
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

    passed = sum(r[2] for r in results)
    print(f"\n{passed}/{len(results)} checks passed in {time.time() - start:.1f}s")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
