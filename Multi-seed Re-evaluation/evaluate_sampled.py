"""
evaluate_sampled.py
===================
WHO    : Sampled-decoding variant of evaluate.py.
PROBLEM: Greedy decoding is deterministic (same output every time), but sampling
         introduces randomness. This script tests how much the score varies when
         we use temperature=0.3 sampling across different random seeds — giving a
         range and standard deviation for the thesis.
INPUT  : --model  path to fine-tuned model folder (e.g. ./qwen05_finetuned)
         --csv    24.csv
         --seed   random seed (42, 123, 456, 789, 2024 — run once per seed)
         --out    output JSON filename
OUTPUT : eval_results_sampled_seed{N}.json  (one file per seed)

Run 5 times:
    python evaluate_sampled.py --model ./qwen05_finetuned --seed 42  --out eval_results_sampled_seed42.json
    python evaluate_sampled.py --model ./qwen05_finetuned --seed 123 --out eval_results_sampled_seed123.json
    python evaluate_sampled.py --model ./qwen05_finetuned --seed 456 --out eval_results_sampled_seed456.json
    python evaluate_sampled.py --model ./qwen05_finetuned --seed 789 --out eval_results_sampled_seed789.json
    python evaluate_sampled.py --model ./qwen05_finetuned --seed 2024 --out eval_results_sampled_seed2024.json
"""

import argparse, csv, json, re, torch
from fractions import Fraction
from transformers import AutoModelForCausalLM, AutoTokenizer

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--model",          required=True)
parser.add_argument("--csv",            default="24.csv")
parser.add_argument("--out",            required=True)
parser.add_argument("--seed",           type=int, required=True)
parser.add_argument("--rank_start",     type=int, default=901)
parser.add_argument("--rank_end",       type=int, default=1000)
parser.add_argument("--max_new_tokens", type=int, default=300)
parser.add_argument("--temperature",    type=float, default=0.3)
parser.add_argument("--top_p",         type=float, default=0.95)
args = parser.parse_args()

# ── Set seed ──────────────────────────────────────────────────────────────────
torch.manual_seed(args.seed)
print(f"Seed: {args.seed} | temperature={args.temperature} | top_p={args.top_p}")

# ── Prompt templates (identical to evaluate.py / train_qwen05.py) ─────────────
SYSTEM_PROMPT = (
    "Use numbers and basic arithmetic operations (+, -, *, /) to obtain 24. "
    "Each step, you are only allowed to choose two of the remaining numbers to obtain a new number.\n"
    "Step 1: Start by considering possible operations for each pair of numbers.\n"
    "Step 2: Try a path (a pair of two numbers), see if the remaining numbers can possibly reach the goal 24. If not, backtrack and attempt another.\n"
    "Step 3: Branch out to try different orders of operations and combinations, evaluating each outcome.\n"
    "Step 4: If one path doesn't lead to a solution, backtrack and try alternative operations.\n\n"
)

IN_CONTEXT_HEADER = (
    "Here are some solved examples:\n\n"
    "Numbers: 4 4 6 8. Target: 24.\n"
    "Use each number exactly once with +, -, *, / to reach 24.\n"
    "Steps:\n"
    "4 + 8 = 12 (left: 4 6 12)\n"
    "6 - 4 = 2 (left: 2 12)\n"
    "2 * 12 = 24 (left: 24)\n"
    "Answer: (6 - 4) * (4 + 8) = 24\n\n"
    "Numbers: 1 4 8 8. Target: 24.\n"
    "Use each number exactly once with +, -, *, / to reach 24.\n"
    "Steps:\n"
    "8 / 4 = 2 (left: 1 2 8)\n"
    "1 + 2 = 3 (left: 3 8)\n"
    "3 * 8 = 24 (left: 24)\n"
    "Answer: (1 + 8 / 4) * 8 = 24\n\n"
    "Numbers: 5 5 5 9. Target: 24.\n"
    "Use each number exactly once with +, -, *, / to reach 24.\n"
    "Steps:\n"
    "5 + 5 = 10 (left: 5 9 10)\n"
    "10 + 5 = 15 (left: 9 15)\n"
    "15 + 9 = 24 (left: 24)\n"
    "Answer: ((5 + 5) + 5) + 9 = 24\n\n"
    "Numbers: 4 9 10 13. Target: 24.\n"
    "Use each number exactly once with +, -, *, / to reach 24.\n"
    "Steps:\n"
    "4 + 9 = 13 (left: 10 13 13)\n"
    "13 - 10 = 3 (left: 3 13)\n"
    "13 + 3 = 16 (left: 16)\n"
    "Backtrack. (to: 4 9 10 13).\n"
    "13 - 10 = 3 (left: 3 4 9)\n"
    "9 - 3 = 6 (left: 4 6)\n"
    "4 * 6 = 24 (left: 24)\n"
    "Answer: 4 * (9 - (13 - 10)) = 24\n\n"
    "Now solve this puzzle:\n"
)

def make_user_content(puzzle):
    return (
        SYSTEM_PROMPT + IN_CONTEXT_HEADER
        + f"Numbers: {puzzle}. Target: 24.\n"
        + "Use each number exactly once with +, -, *, / to reach 24.\n"
        + "Steps:"
    )

# ── Verifier (identical to evaluate.py) ──────────────────────────────────────
def verify_output(puzzle, response_text):
    puzzle_nums   = [Fraction(x) for x in puzzle.strip().split()]
    lines         = [l.strip() for l in response_text.strip().split('\n') if l.strip()]
    step_errors   = []
    steps_checked = steps_ok = 0
    available     = list(puzzle_nums)
    answer_correct = False
    answer_msg    = "No Answer line found"

    for lt in lines:
        if lt.startswith('Backtrack.'):
            bm = re.search(r'\(to:\s*(.*?)\)', lt)
            if bm:
                parsed = []
                for tok in bm.group(1).strip().split():
                    try: parsed.append(Fraction(tok))
                    except: pass
                available = parsed if parsed else list(puzzle_nums)
            else:
                available = list(puzzle_nums)
            continue

        if lt.startswith('Answer:'):
            am = re.match(r'Answer:\s*(.+?)\s*=\s*24', lt)
            if not am:
                answer_msg = f"Cannot parse: {lt!r}"; continue
            expr = am.group(1)
            try:
                expr_f    = re.sub(r'\b(\d+)\b', r'Fraction(\1)', expr)
                result    = eval(expr_f, {"Fraction": Fraction, "__builtins__": {}})
                nums_used = sorted(int(x) for x in re.findall(r'\b\d+\b', expr))
                expected  = sorted(int(x) for x in puzzle.strip().split())
                if result == 24 and nums_used == expected:
                    answer_correct = True; answer_msg = "Correct"
                elif result != 24:
                    answer_msg = f"Evaluates to {float(result):.4g}, not 24"
                else:
                    answer_msg = f"Wrong numbers: {nums_used} vs {expected}"
            except Exception as e:
                answer_msg = f"Eval error: {e}"
            continue

        m = re.match(
            r'(-?[\d.]+)\s*([+\-*/])\s*(-?[\d.]+)\s*=\s*(-?[\d.]+)\s*\(left:\s*(.*?)\)', lt)
        if not m: continue
        steps_checked += 1
        a_s, op, b_s, c_s, _ = m.groups()
        try: a, b, c = Fraction(a_s), Fraction(b_s), Fraction(c_s)
        except: step_errors.append((lt, "parse error")); continue
        ops = {'+': a+b, '-': a-b, '*': a*b, '/': (a/b if b != 0 else None)}
        ec  = ops.get(op)
        if ec is None:
            step_errors.append((lt, "div by zero"))
        elif ec != c:
            step_errors.append((lt, f"{float(a)}{op}{float(b)} != {float(c)}"))
        else:
            steps_ok += 1
            try: available.remove(a); available.remove(b)
            except ValueError:
                step_errors.append((lt, "numbers not in pool")); steps_ok -= 1
                available.append(c); continue
            available.append(c)

    return {
        "step_errors": step_errors, "answer_correct": answer_correct,
        "answer_msg": answer_msg,
        "arithmetic_accuracy": steps_ok / steps_checked if steps_checked else 0.0,
        "steps_checked": steps_checked,
    }

# ── Load puzzles ──────────────────────────────────────────────────────────────
with open(args.csv) as f:
    rows = list(csv.DictReader(f))
test_puzzles = [r["Puzzles"].strip() for r in rows
                if args.rank_start <= int(r["Rank"]) <= args.rank_end]
print(f"Evaluating {len(test_puzzles)} puzzles (ranks {args.rank_start}-{args.rank_end})")

# ── Load model ────────────────────────────────────────────────────────────────
print(f"Loading {args.model} ...")
tokenizer = AutoTokenizer.from_pretrained(args.model)
model     = AutoModelForCausalLM.from_pretrained(
    args.model, device_map="auto",
    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
)
model.eval()
device = next(model.parameters()).device
print(f"Model on {device}\n")

# ── Evaluate with sampling ────────────────────────────────────────────────────
per_puzzle = []
no_answer_count = 0

for i, puzzle in enumerate(test_puzzles):
    torch.manual_seed(args.seed + i)   # per-puzzle seed for full reproducibility
    messages    = [{"role": "user", "content": make_user_content(puzzle)}]
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs      = tokenizer(prompt_text, return_tensors="pt").to(device)
    input_len   = inputs["input_ids"].shape[1]

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=args.temperature,
            top_p=args.top_p,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(out[0][input_len:], skip_special_tokens=True).strip()
    v = verify_output(puzzle, response)
    if v["answer_msg"] == "No Answer line found":
        no_answer_count += 1

    per_puzzle.append({
        "puzzle": puzzle, "response": response,
        "answer_correct": v["answer_correct"], "answer_msg": v["answer_msg"],
        "arithmetic_accuracy": v["arithmetic_accuracy"],
        "steps_checked": v["steps_checked"],
        "step_error_count": len(v["step_errors"]),
    })
    status = "✓" if v["answer_correct"] else "✗"
    print(f"  [{i+1:3d}/100] {status} {puzzle:<15} arith={v['arithmetic_accuracy']:.0%}  step_errs={len(v['step_errors'])}")

# ── Save ──────────────────────────────────────────────────────────────────────
n       = len(per_puzzle)
correct = sum(1 for r in per_puzzle if r["answer_correct"])
avg_acc = sum(r["arithmetic_accuracy"] for r in per_puzzle) / n

summary = {
    "model": args.model, "csv": args.csv,
    "decoding": "sampled",
    "seed": args.seed, "temperature": args.temperature, "top_p": args.top_p,
    "rank_start": args.rank_start, "rank_end": args.rank_end,
    "n_puzzles": n, "n_correct": correct,
    "success_rate_pct": round(correct / n * 100, 1),
    "no_answer_count": no_answer_count,
    "avg_arithmetic_acc": round(avg_acc, 4),
    "total_step_errors": sum(r["step_error_count"] for r in per_puzzle),
    "per_puzzle": per_puzzle,
}
with open(args.out, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print(f"SUMMARY  (seed={args.seed}, temp={args.temperature})")
print(f"{'='*60}")
print(f"  Correct (= 24)  : {correct}/{n} ({correct/n*100:.1f}%)")
print(f"  No-answer count : {no_answer_count}")
print(f"Results saved -> {args.out}")
