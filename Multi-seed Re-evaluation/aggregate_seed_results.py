"""
aggregate_seed_results.py
=========================
WHO    : Aggregates results from all greedy and sampled evaluation runs.
PROBLEM: After running evaluate.py 3 times and evaluate_sampled.py 5 times,
         this script reads all 8 result files and produces the thesis summary
         sentence: stability of greedy decoding + mean/std of sampled decoding.
INPUT  : eval_results_run1.json, eval_results_run2.json, eval_results_run3.json
         eval_results_sampled_seed42.json, ..._seed123.json, ..._seed456.json,
         ..._seed789.json, ..._seed2024.json
OUTPUT : Prints thesis-ready summary sentence to console.
         Saves full breakdown to seed_aggregation_results.json
"""

import json, os, statistics

# ── Greedy runs (3 runs of evaluate.py) ──────────────────────────────────────
greedy_files = [
    "eval_results_run1.json",
    "eval_results_run2.json",
    "eval_results_run3.json",
]

# ── Sampled runs (5 seeds of evaluate_sampled.py) ─────────────────────────────
sampled_files = [
    ("eval_results_sampled_seed42.json",   42),
    ("eval_results_sampled_seed123.json",  123),
    ("eval_results_sampled_seed456.json",  456),
    ("eval_results_sampled_seed789.json",  789),
    ("eval_results_sampled_seed2024.json", 2024),
]

print("=" * 65)
print("SEED AGGREGATION RESULTS")
print("=" * 65)

# ── Load greedy runs ──────────────────────────────────────────────────────────
greedy_scores = []
print("\n--- Greedy Decoding (do_sample=False) ---")
for fpath in greedy_files:
    if os.path.exists(fpath):
        with open(fpath) as f:
            d = json.load(f)
        score = d["success_rate_pct"]
        greedy_scores.append(score)
        print(f"  {fpath}: {score}%  ({d['n_correct']}/{d['n_puzzles']})")
    else:
        print(f"  {fpath}: NOT FOUND — run evaluate.py first")

if len(greedy_scores) == 3:
    all_same = len(set(greedy_scores)) == 1
    print(f"\n  All 3 greedy runs identical: {'YES ✓' if all_same else 'NO — unexpected variance!'}")
    greedy_summary = f"Greedy decoding: {greedy_scores[0]}% (deterministic, confirmed across 3 runs)"
else:
    greedy_summary = f"Greedy decoding: only {len(greedy_scores)}/3 runs found"
    all_same = None

# ── Load sampled runs ─────────────────────────────────────────────────────────
sampled_scores = []
print("\n--- Sampled Decoding (temperature=0.3, top_p=0.95) ---")
for fpath, seed in sampled_files:
    if os.path.exists(fpath):
        with open(fpath) as f:
            d = json.load(f)
        score = d["success_rate_pct"]
        sampled_scores.append(score)
        print(f"  seed={seed:4d}  {fpath}: {score}%  ({d['n_correct']}/{d['n_puzzles']})")
    else:
        print(f"  seed={seed:4d}  {fpath}: NOT FOUND — run evaluate_sampled.py --seed {seed} first")

if sampled_scores:
    mean_s = statistics.mean(sampled_scores)
    std_s  = statistics.stdev(sampled_scores) if len(sampled_scores) > 1 else 0.0
    min_s  = min(sampled_scores)
    max_s  = max(sampled_scores)
    print(f"\n  Mean  : {mean_s:.1f}%")
    print(f"  Std   : {std_s:.1f}%")
    print(f"  Range : {min_s:.0f}% – {max_s:.0f}%")
    sampled_summary = (
        f"Sampled decoding (temp=0.3): mean {mean_s:.1f}% ± {std_s:.1f}% "
        f"across {len(sampled_scores)} seeds (range: {min_s:.0f}%–{max_s:.0f}%)"
    )
else:
    sampled_summary = "Sampled decoding: no results found"

# ── Thesis-ready summary ──────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("THESIS SUMMARY SENTENCE")
print("=" * 65)
thesis_line = greedy_summary + ". " + sampled_summary + "."
print(f"\n  \"{thesis_line}\"")

# ── Save aggregation ──────────────────────────────────────────────────────────
output = {
    "greedy_scores":    greedy_scores,
    "greedy_all_same":  all_same,
    "sampled_scores":   sampled_scores,
    "sampled_mean":     round(statistics.mean(sampled_scores), 2) if sampled_scores else None,
    "sampled_std":      round(statistics.stdev(sampled_scores), 2) if len(sampled_scores) > 1 else 0.0,
    "sampled_min":      min(sampled_scores) if sampled_scores else None,
    "sampled_max":      max(sampled_scores) if sampled_scores else None,
    "thesis_sentence":  thesis_line,
}
with open("seed_aggregation_results.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"\nFull breakdown saved -> seed_aggregation_results.json")
