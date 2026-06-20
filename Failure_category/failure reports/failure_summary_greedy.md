# Failure Mode Analysis

Model evaluated on 100 puzzles (Game of 24, ranks 901–1000).  
Correct: **19/100 (19%)** | Failures analysed: **81**

## Failure Categories

| Category | Count | % of failures |
|---|---|---|
| no_answer_line | 37 | 45.7% |
| hit_token_limit | 36 | 44.4% |
| excessive_backtracking | 5 | 6.2% |
| wrong_final_answer | 1 | 1.2% |
| malformed_answer | 2 | 2.5% |
| other | 0 | 0.0% |

## Backtracking in Correct Answers

Of the 19 correct answers:
- **14** (74%) included at least one `Backtrack.` step
- **5** (26%) were solved directly without backtracking