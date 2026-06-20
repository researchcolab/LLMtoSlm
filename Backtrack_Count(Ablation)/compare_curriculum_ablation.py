"""
compare_curriculum_ablation.py
===============================
WHO    : Prints the final ablation comparison table (Prompt 4, Task 4).
PROBLEM: Does the deliberate 30/30/25/15 backtrack curriculum outperform
         simpler fixed-count alternatives?
INPUT  : eval_results.json               — original augmented model (greedy, 19%)
         eval_results_fixed_1bt.json     — all-1-backtrack model
         eval_results_fixed_2bt.json     — all-2-backtrack model
         eval_results_balanced_equal.json — balanced 25/25/25/25 model
OUTPUT : curriculum_ablation_results.md  — markdown table for thesis
"""

import json, sys
from pathlib import Path

RESULT_FILES = {
    "Original mix (30/30/25/15)": "eval_results.json",
    "All 1-backtrack (100%)":     "eval_results_fixed_1bt.json",
    "All 2-backtrack (100%)":     "eval_results_fixed_2bt.json",
    "Balanced equal (25/25/25/25)": "eval_results_balanced_equal.json",
}

rows = []
for label, fname in RESULT_FILES.items():
    p = Path(fname)
    if not p.exists():
        rows.append((label, "NOT RUN", "NOT RUN", fname))
        continue
    with open(p) as f:
        data = json.load(f)
    puzzles      = data["per_puzzle"]
    n_total      = len(puzzles)
    n_correct    = sum(1 for p in puzzles if p["answer_correct"])
    no_answer    = sum(1 for p in puzzles if not p.get("answer_correct") and "Answer:" not in p.get("response",""))
    success_pct  = f"{n_correct/n_total*100:.0f}% ({n_correct}/{n_total})"
    no_ans_pct   = f"{no_answer/n_total*100:.0f}% ({no_answer}/{n_total})"
    rows.append((label, success_pct, no_ans_pct, fname))

# ── Console table ─────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print("CURRICULUM ABLATION COMPARISON")
print(f"{'='*75}")
print(f"{'Dataset composition':<35} {'Success rate':>14} {'No-answer rate':>16}")
print("-" * 75)
for label, succ, noans, _ in rows:
    print(f"  {label:<33} {succ:>14} {noans:>16}")

# ── Markdown ──────────────────────────────────────────────────────────────────
md = [
    "# Curriculum Ablation Results\n",
    "Comparison of different backtrack-count compositions, all trained on",
    "Qwen2.5-0.5B-Instruct with identical hyperparameters (n=100 test puzzles, ranks 901–1000).\n",
    "| Dataset composition | Success rate | No-answer rate |",
    "|---|---|---|",
]
for label, succ, noans, _ in rows:
    md.append(f"| {label} | {succ} | {noans} |")

md.append("\n## Notes\n")
md.append("- All datasets contain 1487 examples (matched to original size).")
md.append("- Fixed-1bt and fixed-2bt datasets require sampling with replacement")
md.append("  (446 and 372 unique examples available respectively).")
md.append("- Balanced-equal: 25% each of 0/1/2/3+ backtrack examples (148 duplicates in 3+ bucket).")
md.append("- Original mix: 30% clean / 30% 1-bt / 25% 2-bt / 15% 3+-bt.")

with open("curriculum_ablation_results.md", "w") as f:
    f.write("\n".join(md))
print(f"\nMarkdown saved → curriculum_ablation_results.md")
