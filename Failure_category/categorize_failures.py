"""
categorize_failures.py
======================
WHO    : Categorizes WHY the fine-tuned Qwen2.5-0.5B-Instruct model fails
         on the puzzles it gets wrong.
PROBLEM: Knowing the score is 24% is not enough for a thesis — you need to
         explain the failure modes. Are failures because the model gives no
         answer at all? Wrong arithmetic? Too much backtracking?
INPUT  : eval_results.json  — per-puzzle results with fields:
           rank, puzzle, response, answer (extracted Answer line or null),
           correct (true/false)
OUTPUT : failure_categories.json  — full categorized results
         failure_summary.md       — markdown table for thesis
"""

import json, re
from fractions import Fraction
from collections import Counter

INPUT_FILE = "eval_results_sampled_seed2024.json"
CAT_OUTPUT = "failure_categories_sampled_seed2024.json"
MD_OUTPUT  = "failure_summary_sampled_seed2024.md"

# ── Load results ───────────────────────────────────────────────────────────────
with open(INPUT_FILE) as f:
    data = json.load(f)

# Support both flat list and {"per_puzzle": [...]} formats
if isinstance(data, list):
    all_puzzles = data
else:
    all_puzzles = data.get("per_puzzle", data.get("results", []))

# Normalise field names: accept "correct" or "answer_correct"
def is_correct(p):
    return p.get("correct", p.get("answer_correct", False))

n_total   = len(all_puzzles)
n_correct = sum(1 for p in all_puzzles if is_correct(p))
failures  = [p for p in all_puzzles if not is_correct(p)]
n_failures = len(failures)

print(f"Total puzzles : {n_total}")
print(f"Correct       : {n_correct}")
print(f"Failures      : {n_failures}")

# ── Categorise each failure ────────────────────────────────────────────────────
def categorize(puzzle_nums, response):
    has_answer_line = "Answer:" in response
    n_backtracks    = response.count("Backtrack.")

    # Priority a: no Answer line at all
    if not has_answer_line:
        # Priority b: check if response looks cut off mid-step (hit_token_limit)
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        last  = lines[-1] if lines else ""
        # Cut-off: last line is a partial arithmetic step (has "=" but no "(left:")
        # or is a partial Backtrack line (started but not ended with ".")
        is_cutoff = (
            bool(re.match(r"-?[\d.]+\s*[+\-*/]\s*-?[\d.]+\s*=", last))
            and "(left:" not in last
        ) or (last.startswith("Backtrack") and not last.endswith(")."))
        if is_cutoff:
            return "hit_token_limit"
        return "no_answer_line"

    # Priority c: excessive backtracking (3+ Backtrack. occurrences)
    if n_backtracks >= 3:
        return "excessive_backtracking"

    # Priority d/e: Answer line present — try to parse
    am = re.search(r"Answer:\s*(.+?)\s*=\s*24", response)
    if not am:
        return "malformed_answer"

    expr = am.group(1)
    try:
        expr_f    = re.sub(r"\b(\d+)\b", r"Fraction(\1)", expr)
        result    = eval(expr_f, {"Fraction": Fraction, "__builtins__": {}})
        nums_used = sorted(int(x) for x in re.findall(r"\b\d+\b", expr))
        expected  = sorted(int(x) for x in str(puzzle_nums).strip().split())
        if result == 24 and nums_used == expected:
            return "other"   # shouldn't happen — we're only in failures
        return "wrong_final_answer"
    except Exception:
        return "malformed_answer"


categorized = []
for p in failures:
    puzzle_str = p.get("puzzle", "")
    response   = p.get("response", "")
    cat        = categorize(puzzle_str, response)
    categorized.append({
        "rank":     p.get("rank", "?"),
        "puzzle":   puzzle_str,
        "category": cat,
        "response": response,
        "answer":   p.get("answer", None),
    })

# ── Summary table ──────────────────────────────────────────────────────────────
counts = Counter(c["category"] for c in categorized)
categories = [
    "no_answer_line",
    "hit_token_limit",
    "excessive_backtracking",
    "wrong_final_answer",
    "malformed_answer",
    "other",
]

print(f"\n{'='*65}")
print(f"FAILURE CATEGORIZATION  ({n_failures} failures out of {n_total})")
print(f"{'='*65}")
print(f"{'Category':<25} {'Count':>6} {'% of failures':>14}")
print("-" * 50)
for cat in categories:
    c   = counts.get(cat, 0)
    pct = c / n_failures * 100 if n_failures else 0
    print(f"  {cat:<23} {c:>6} {pct:>13.1f}%")

# ── Examples per category ──────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("EXAMPLES PER CATEGORY (first 2 each)")
print("=" * 65)
seen = Counter()
for item in categorized:
    cat = item["category"]
    if seen[cat] < 2:
        print(f"\n  [{cat}] rank={item['rank']} puzzle: {item['puzzle']}")
        snippet = item["response"].replace("\n", " ")[:200]
        print(f"  Response (first 200 chars): {snippet!r}")
        seen[cat] += 1

# ── Backtracking in correct answers ───────────────────────────────────────────
successes        = [p for p in all_puzzles if is_correct(p)]
bt_in_success    = sum(1 for p in successes if "Backtrack." in p.get("response", ""))
no_bt_in_success = len(successes) - bt_in_success

print(f"\n{'='*65}")
print(f"BACKTRACKING IN CORRECT ANSWERS (n={len(successes)})")
print(f"{'='*65}")
if successes:
    print(f"  With backtrack step   : {bt_in_success}/{len(successes)} "
          f"({bt_in_success/len(successes)*100:.0f}%)")
    print(f"  Without backtrack step: {no_bt_in_success}/{len(successes)} "
          f"({no_bt_in_success/len(successes)*100:.0f}%)")
else:
    print("  No correct answers found.")

# ── Save JSON ──────────────────────────────────────────────────────────────────
output = {
    "n_total":    n_total,
    "n_correct":  n_correct,
    "n_failures": n_failures,
    "category_counts": dict(counts),
    "backtrack_in_correct":    bt_in_success,
    "no_backtrack_in_correct": no_bt_in_success,
    "failures": categorized,
}
with open(CAT_OUTPUT, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nFull results saved → {CAT_OUTPUT}")

# ── Write markdown ─────────────────────────────────────────────────────────────
md = []
md.append("# Failure Mode Analysis\n")
md.append(f"Model evaluated on {n_total} puzzles (Game of 24, ranks 901–1000).  ")
md.append(f"Correct: **{n_correct}/{n_total} ({n_correct}%)** | Failures analysed: **{n_failures}**\n")

md.append("## Failure Categories\n")
md.append("| Category | Count | % of failures |")
md.append("|---|---|---|")
for cat in categories:
    c   = counts.get(cat, 0)
    pct = c / n_failures * 100 if n_failures else 0
    md.append(f"| {cat} | {c} | {pct:.1f}% |")

md.append("\n## Backtracking in Correct Answers\n")
if successes:
    md.append(f"Of the {len(successes)} correct answers:")
    md.append(f"- **{bt_in_success}** ({bt_in_success/len(successes)*100:.0f}%) "
              f"included at least one `Backtrack.` step")
    md.append(f"- **{no_bt_in_success}** ({no_bt_in_success/len(successes)*100:.0f}%) "
              f"were solved directly without backtracking")

with open(MD_OUTPUT, "w") as f:
    f.write("\n".join(md))
print(f"Markdown summary saved → {MD_OUTPUT}")
