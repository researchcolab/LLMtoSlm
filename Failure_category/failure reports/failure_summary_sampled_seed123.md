# Failure Mode Analysis

Model evaluated on 100 puzzles (Game of 24, ranks 901–1000).  
Correct: **20/100 (20%)** | Failures analysed: **80**

## Failure Categories

| Category | Count | % of failures |
|---|---|---|
| no_answer_line | 30 | 37.5% |
| hit_token_limit | 38 | 47.5% |
| excessive_backtracking | 9 | 11.2% |
| wrong_final_answer | 2 | 2.5% |
| malformed_answer | 1 | 1.2% |
| other | 0 | 0.0% |

## Backtracking in Correct Answers

Of the 20 correct answers:
- **15** (75%) included at least one `Backtrack.` step
- **5** (25%) were solved directly without backtracking