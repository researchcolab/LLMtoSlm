"""
make_fixed_backtrack_datasets.py
=================================
WHO    : Builds three alternative training sets for the backtrack-count
         curriculum ablation (Prompt 4).
PROBLEM: Does the specific 30/30/25/15 curriculum mix actually matter, or
         would any reasonable fixed composition work just as well?
INPUT  : training_data_augmented_v2.jsonl  (1487 examples)
OUTPUT : training_data_fixed_1bt.jsonl     — ~100% 1-backtrack examples
         training_data_fixed_2bt.jsonl     — ~100% 2-backtrack examples
         training_data_balanced_equal.jsonl — 25% each of 0/1/2/3+ bt

Source pool sizes (from augmented_v2):
  clean (0 bt) : 446
  1-backtrack  : 446
  2-backtrack  : 372
  3+-backtrack : 223
  Total        : 1487  ← target size for each dataset
"""

import json, random
from collections import Counter

SEED        = 42
SOURCE_FILE = "training_data_augmented_v2.jsonl"
TARGET_SIZE = 1487   # match original dataset size

random.seed(SEED)

# ── Load and bucket ────────────────────────────────────────────────────────────
print("Loading source data...")
pools = {0: [], 1: [], 2: [], "3+": []}
with open(SOURCE_FILE) as f:
    for line in f:
        r = json.loads(line)
        n = r.get("n_backtracks", None)
        if n is None or r.get("example_type") == "clean":
            pools[0].append(r)
        elif n == 1:
            pools[1].append(r)
        elif n == 2:
            pools[2].append(r)
        else:
            pools["3+"].append(r)

for k, v in pools.items():
    print(f"  Pool n_backtracks={k}: {len(v)} examples")
print()


def sample_with_replacement(pool, n, rng):
    """Fill n slots from pool, sampling with replacement if needed."""
    unique   = min(n, len(pool))
    selected = rng.sample(pool, unique)
    dupes    = 0
    while len(selected) < n:
        selected.append(rng.choice(pool))
        dupes += 1
    return selected, dupes


def write_jsonl(rows, path):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def print_composition(rows, label):
    counts = Counter()
    for r in rows:
        n = r.get("n_backtracks", None)
        if n is None or r.get("example_type") == "clean":
            counts[0] += 1
        elif n == 1:
            counts[1] += 1
        elif n == 2:
            counts[2] += 1
        else:
            counts["3+"] += 1
    total = len(rows)
    print(f"  {label} ({total} total):")
    for k in [0, 1, 2, "3+"]:
        c = counts.get(k, 0)
        print(f"    n_bt={k}: {c:4d} ({c/total*100:5.1f}%)")
    print()


rng = random.Random(SEED)

# ── Dataset A: all_one_bt ─────────────────────────────────────────────────────
print("=" * 60)
print("Building training_data_fixed_1bt.jsonl (all 1-backtrack)")
rows_1bt, dupes_1bt = sample_with_replacement(pools[1], TARGET_SIZE, rng)
rng.shuffle(rows_1bt)
write_jsonl(rows_1bt, "training_data_fixed_1bt.jsonl")
print(f"  Duplicates introduced: {dupes_1bt}")
print_composition(rows_1bt, "fixed_1bt")

# ── Dataset B: all_two_bt ─────────────────────────────────────────────────────
print("=" * 60)
print("Building training_data_fixed_2bt.jsonl (all 2-backtrack)")
rows_2bt, dupes_2bt = sample_with_replacement(pools[2], TARGET_SIZE, rng)
rng.shuffle(rows_2bt)
write_jsonl(rows_2bt, "training_data_fixed_2bt.jsonl")
print(f"  Duplicates introduced: {dupes_2bt}")
print_composition(rows_2bt, "fixed_2bt")

# ── Dataset C: balanced_equal (25/25/25/25) ───────────────────────────────────
print("=" * 60)
print("Building training_data_balanced_equal.jsonl (25% each)")

per_bucket = TARGET_SIZE // 4          # 371
remainder  = TARGET_SIZE - per_bucket * 4  # 3 extra (give to largest pools)

bucket_sizes = {0: per_bucket, 1: per_bucket, 2: per_bucket, "3+": per_bucket}
# Distribute remainder to first buckets by pool size (largest first)
order = sorted(bucket_sizes.keys(), key=lambda k: len(pools[k]), reverse=True)
for i in range(remainder):
    bucket_sizes[order[i]] += 1

rows_bal = []
for k in [0, 1, 2, "3+"]:
    n = bucket_sizes[k]
    sampled, d = sample_with_replacement(pools[k], n, rng)
    rows_bal.extend(sampled)
    if d:
        print(f"  Duplicates for n_bt={k}: {d}")
rng.shuffle(rows_bal)
write_jsonl(rows_bal, "training_data_balanced_equal.jsonl")
print_composition(rows_bal, "balanced_equal")

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Original mix (30/30/25/15):    1487 examples")
print(f"training_data_fixed_1bt.jsonl: {len(rows_1bt)} examples  "
      f"({dupes_1bt} duplicates from 446-example pool)")
print(f"training_data_fixed_2bt.jsonl: {len(rows_2bt)} examples  "
      f"({dupes_2bt} duplicates from 372-example pool)")
print(f"training_data_balanced_equal.jsonl: {len(rows_bal)} examples")
print("\nDone. Three dataset files written.")
