"""
significance_tests.py
=====================
WHO    : Tests whether performance differences between models are statistically
         real or could just be due to chance (n=100 test puzzles).
PROBLEM: With only 100 test puzzles, a difference of e.g. 24% vs 19% might look
         meaningful but could be noise. This script proves which differences are
         statistically significant.
INPUT  : Hardcoded result counts from eval_results.json, eval_results_clean_only.json,
         and thesis comparison numbers (babysitting paper).
OUTPUT : Console summary + significance_results.md (paste directly into thesis Chapter 5)
"""

# ── Result counts (sourced from eval results and thesis) ──────────────────────
# From your Teacher evaluation
my_teacher_solved       = 89;  my_teacher_total       = 100

# From eval_results.json (Qwen trained on full 1487 augmented examples)
my_student_qwen_solved  = 24;  my_student_qwen_total  = 100

# From eval_results_clean_only.json (Qwen trained on 446 clean examples only)
my_student_clean_solved = 11;  my_student_clean_total = 100

# SmolLM-360M — failed to learn the task
my_student_smollm_solved = 0;  my_student_smollm_total = 100

# Babysitting paper comparison numbers
babysitting_teacher_solved  = 19;  babysitting_teacher_total  = 100
babysitting_student_solved  =  9;  babysitting_student_total  = 100

# ── Imports ───────────────────────────────────────────────────────────────────
import math
from scipy.stats import fisher_exact
from statsmodels.stats.proportion import proportions_ztest, proportion_confint

# ── Wilson 95% CI ─────────────────────────────────────────────────────────────
def wilson_ci(solved, total, confidence=0.95):
    lo, hi = proportion_confint(solved, total, alpha=1-confidence, method='wilson')
    pct     = solved / total * 100
    return pct, lo * 100, hi * 100

# ── Two-proportion z-test + Fisher's exact ────────────────────────────────────
def compare(label, s1, n1, s2, n2):
    p1 = s1 / n1
    p2 = s2 / n2

    # Two-proportion z-test
    count  = [s1, s2]
    nobs   = [n1, n2]
    z, p_z = proportions_ztest(count, nobs)

    # Fisher's exact test (2x2 contingency table)
    table  = [[s1, n1 - s1], [s2, n2 - s2]]
    _, p_f = fisher_exact(table)

    sig_z = "significant (p<0.05)" if p_z < 0.05 else "NOT significant — could be chance"
    sig_f = "significant (p<0.05)" if p_f < 0.05 else "NOT significant — could be chance"

    print(f"\n{'─'*65}")
    print(f"COMPARISON: {label}")
    print(f"  {p1:.0%} ({s1}/{n1})  vs  {p2:.0%} ({s2}/{n2})")
    print(f"  Z-test  : z={z:+.3f}, p={p_z:.4f}  → {sig_z}")
    print(f"  Fisher  : p={p_f:.4f}             → {sig_f}")

    return {
        "label": label,
        "p1": f"{p1:.0%} ({s1}/{n1})",
        "p2": f"{p2:.0%} ({s2}/{n2})",
        "z_stat": round(z, 3),
        "p_z": round(p_z, 4),
        "p_fisher": round(p_f, 4),
        "verdict": sig_f,
    }

# ── Run comparisons ───────────────────────────────────────────────────────────
print("=" * 65)
print("STATISTICAL SIGNIFICANCE TESTS")
print("=" * 65)

results = []

results.append(compare(
    "My teacher (89%) vs Babysitting teacher (19%)",
    my_teacher_solved, my_teacher_total,
    babysitting_teacher_solved, babysitting_teacher_total,
))

results.append(compare(
    "My student Qwen (24%) vs Babysitting student (9%)",
    my_student_qwen_solved, my_student_qwen_total,
    babysitting_student_solved, babysitting_student_total,
))

results.append(compare(
    "My student Qwen (24%) vs Babysitting teacher (19%)\n  [Does student beat their teacher?]",
    my_student_qwen_solved, my_student_qwen_total,
    babysitting_teacher_solved, babysitting_teacher_total,
))

results.append(compare(
    "My student Qwen (24%) vs SmolLM (0%)",
    my_student_qwen_solved, my_student_qwen_total,
    my_student_smollm_solved, my_student_smollm_total,
))

results.append(compare(
    "Augmented training (24%) vs Clean-only training (11%)\n  [Does backtracking augmentation help?]",
    my_student_qwen_solved, my_student_qwen_total,
    my_student_clean_solved, my_student_clean_total,
))

# ── Wilson confidence intervals ───────────────────────────────────────────────
print(f"\n{'='*65}")
print("95% CONFIDENCE INTERVALS (Wilson score)")
print("=" * 65)

proportions = [
    ("My Teacher",                    my_teacher_solved,        my_teacher_total),
    ("My Student Qwen (augmented)",   my_student_qwen_solved,   my_student_qwen_total),
    ("My Student Qwen (clean only)",  my_student_clean_solved,  my_student_clean_total),
    ("My Student SmolLM",             my_student_smollm_solved, my_student_smollm_total),
    ("Babysitting Teacher",           babysitting_teacher_solved,babysitting_teacher_total),
    ("Babysitting Student",           babysitting_student_solved,babysitting_student_total),
]

ci_rows = []
for name, s, n in proportions:
    pct, lo, hi = wilson_ci(s, n)
    print(f"  {name:<35} {pct:.0f}%  (95% CI: [{lo:.1f}%, {hi:.1f}%])")
    ci_rows.append((name, pct, lo, hi))

# ── Write markdown for thesis ─────────────────────────────────────────────────
md = []
md.append("# Statistical Significance Tests\n")
md.append("All tests use n=100 puzzles (Game of 24, ranks 901–1000).\n")

md.append("## Pairwise Comparisons\n")
md.append("| Comparison | Proportion 1 | Proportion 2 | Z-test p | Fisher p | Verdict |")
md.append("|---|---|---|---|---|---|")
for r in results:
    label = r["label"].replace("\n  ", " ")
    md.append(f"| {label} | {r['p1']} | {r['p2']} | {r['p_z']} | {r['p_fisher']} | {r['verdict']} |")

md.append("\n## 95% Confidence Intervals (Wilson Score)\n")
md.append("| Model | Success Rate | 95% CI Lower | 95% CI Upper |")
md.append("|---|---|---|---|")
for name, pct, lo, hi in ci_rows:
    md.append(f"| {name} | {pct:.0f}% | {lo:.1f}% | {hi:.1f}% |")

md.append("\n## Key Findings\n")
md.append("- **My teacher vs babysitting teacher**: tests whether the tree-of-thought teacher is better than a one-step teacher.")
md.append("- **My student vs babysitting student**: tests whether distillation from a better teacher produces a better student.")
md.append("- **My student vs babysitting teacher**: tests whether the student surpasses the weaker teacher.")
md.append("- **Augmented vs clean-only**: tests whether backtracking augmentation was responsible for the improvement.")

with open("significance_results.md", "w") as f:
    f.write("\n".join(md))

print(f"\n{'='*65}")
print("Markdown table saved → significance_results.md")
print("Paste directly into thesis Chapter 5.")
