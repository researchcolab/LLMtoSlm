# Curriculum Ablation Results

Comparison of different backtrack-count compositions, all trained on
Qwen2.5-0.5B-Instruct with identical hyperparameters (n=100 test puzzles, ranks 901–1000).

| Dataset composition | Success rate | No-answer rate |
|---|---|---|
| Original mix (30/30/25/15) | 19% (19/100) | 73% (73/100) |
| All 1-backtrack (100%) | 13% (13/100) | 26% (26/100) |
| All 2-backtrack (100%) | 9% (9/100) | 54% (54/100) |
| Balanced equal (25/25/25/25) | 16% (16/100) | 77% (77/100) |

## Notes

- All datasets contain 1487 examples (matched to original size).
- Fixed-1bt and fixed-2bt datasets require sampling with replacement
  (446 and 372 unique examples available respectively).
- Balanced-equal: 25% each of 0/1/2/3+ backtrack examples (148 duplicates in 3+ bucket).
- Original mix: 30% clean / 30% 1-bt / 25% 2-bt / 15% 3+-bt.