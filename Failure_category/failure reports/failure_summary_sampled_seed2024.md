# Failure Mode Analysis

Model evaluated on 100 puzzles (Game of 24, ranks 901–1000).  
Correct: **23/100 (23%)** | Failures analysed: **77**

## Failure Categories

| Category | Count | % of failures |
|---|---|---|
| no_answer_line | 37 | 48.1% |
| hit_token_limit | 33 | 42.9% |
| excessive_backtracking | 6 | 7.8% |
| wrong_final_answer | 1 | 1.3% |
| malformed_answer | 0 | 0.0% |
| other | 0 | 0.0% |

## Backtracking in Correct Answers

Of the 23 correct answers:
- **18** (78%) included at least one `Backtrack.` step
- **5** (22%) were solved directly without backtracking