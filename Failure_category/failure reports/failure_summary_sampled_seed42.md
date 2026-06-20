# Failure Mode Analysis

Model evaluated on 100 puzzles (Game of 24, ranks 901–1000).  
Correct: **16/100 (16%)** | Failures analysed: **84**

## Failure Categories

| Category | Count | % of failures |
|---|---|---|
| no_answer_line | 34 | 40.5% |
| hit_token_limit | 40 | 47.6% |
| excessive_backtracking | 6 | 7.1% |
| wrong_final_answer | 0 | 0.0% |
| malformed_answer | 4 | 4.8% |
| other | 0 | 0.0% |

## Backtracking in Correct Answers

Of the 16 correct answers:
- **14** (88%) included at least one `Backtrack.` step
- **2** (12%) were solved directly without backtracking