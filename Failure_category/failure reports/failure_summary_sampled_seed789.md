# Failure Mode Analysis

Model evaluated on 100 puzzles (Game of 24, ranks 901–1000).  
Correct: **23/100 (23%)** | Failures analysed: **77**

## Failure Categories

| Category | Count | % of failures |
|---|---|---|
| no_answer_line | 27 | 35.1% |
| hit_token_limit | 35 | 45.5% |
| excessive_backtracking | 8 | 10.4% |
| wrong_final_answer | 2 | 2.6% |
| malformed_answer | 5 | 6.5% |
| other | 0 | 0.0% |

## Backtracking in Correct Answers

Of the 23 correct answers:
- **20** (87%) included at least one `Backtrack.` step
- **3** (13%) were solved directly without backtracking