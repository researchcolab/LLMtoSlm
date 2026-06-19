# Statistical Significance Tests

All tests use n=100 puzzles (Game of 24, ranks 901–1000).

## Pairwise Comparisons

| Comparison | Proportion 1 | Proportion 2 | Z-test p | Fisher p | Verdict |
|---|---|---|---|---|---|
| My teacher (89%) vs Babysitting teacher (19%) | 89% (89/100) | 19% (19/100) | 0.0 | 0.0 | significant (p<0.05) |
| My student Qwen (24%) vs Babysitting student (9%) | 24% (24/100) | 9% (9/100) | 0.0043 | 0.007 | significant (p<0.05) |
| My student Qwen (24%) vs Babysitting teacher (19%) [Does student beat their teacher?] | 24% (24/100) | 19% (19/100) | 0.3895 | 0.4915 | NOT significant — could be chance |
| My student Qwen (24%) vs SmolLM (0%) | 24% (24/100) | 0% (0/100) | 0.0 | 0.0 | significant (p<0.05) |
| Augmented training sampling (24%) vs Clean-only training sampling (10%) [Does backtracking augmentation help?] | 24% (24/100) | 10% (10/100) | 0.0084 | 0.0136 | significant (p<0.05) |
| Augmented training greedy (19%) vs Clean-only training greedy (11%) [Does backtracking augmentation help?] | 19% (19/100) | 11% (11/100) | 0.1131 | 0.1649 | NOT significant — could be chance |

## 95% Confidence Intervals (Wilson Score)

| Model | Success Rate | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| My Teacher | 89% | 81.4% | 93.7% |
| My Student Qwen (augmented) sampling | 24% | 16.7% | 33.2% |
| My Student Qwen (clean only) sampling | 10% | 5.5% | 17.4% |
| My Student SmolLM | 0% | 0.0% | 3.7% |
| Babysitting Teacher | 19% | 12.5% | 27.8% |
| Babysitting Student | 9% | 4.8% | 16.2% |

## Key Findings

- **My teacher vs babysitting teacher**: tests whether the tree-of-thought teacher is better than a one-step teacher.
- **My student vs babysitting student**: tests whether distillation from a better teacher produces a better student.
- **My student vs babysitting teacher**: tests whether the student surpasses the weaker teacher.
- **Augmented vs clean-only**: tests whether backtracking augmentation was responsible for the improvement.