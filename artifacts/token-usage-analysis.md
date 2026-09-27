# Token Usage Analysis

## Setup

- Task: `django__django-15368`
- Model: `deepseek-flash`
- Compaction threshold: 6,000 estimated active tokens
- Recent steps retained verbatim: 1
- Compaction summary limit: 1,200 tokens
- Baseline: compaction disabled
- Validation: both patches passed 1/1 FAIL_TO_PASS and 29/29 PASS_TO_PASS tests

Usage for the compacted condition includes both normal ReAct action calls and
the additional model calls that generated working-memory summaries. This avoids
understating the cost of compaction. The two runs are stochastic, so step counts
differ and the comparison is an observed sample rather than a controlled claim
that compaction always changes the number of actions.

## Results

| Metric | Compacted | No-compaction baseline |
|---|---:|---:|
| ReAct action steps | 36 | 21 |
| Compaction calls | 10 | 0 |
| Action prompt tokens | 159,655 | 314,314 |
| Compaction prompt tokens | 55,108 | 0 |
| Combined prompt tokens | 214,763 | 314,314 |
| Action completion tokens | 9,147 | 6,317 |
| Compaction completion tokens | 10,141 | 0 |
| Combined completion tokens | 19,288 | 6,317 |
| Combined total tokens | 234,051 | 320,631 |
| Average action prompt tokens | 4,434.9 | 14,967.3 |
| Maximum action prompt tokens | 6,098 | 23,067 |
| Patch passed evaluation | Yes | Yes |

The compacted run used 99,551 fewer prompt tokens (31.7% less) and 86,580
fewer total tokens (27.0% less), despite taking 15 more ReAct action steps and
paying for 10 separate summary calls. Its maximum action prompt was 73.6%
smaller than the baseline maximum.

Across the 10 compaction events, the estimated active prompt fell from an
average of 5,657.8 tokens before compaction to 2,400.7 afterward, an average
reduction of 3,257.1 tokens. Every recorded event reduced the estimated active
context. The resulting compacted and baseline patches were identical.

## Observations

Without compaction, every action request retransmitted the accumulating command
history and tool output. The prompt therefore grew to 23,067 tokens even though
the baseline happened to finish in fewer steps. With compaction, old interaction
prefixes were repeatedly replaced by concise working memory while the original
instructions and latest complete assistant/tool step remained verbatim. This
kept action prompts near the 6,000-token threshold.

Compaction did not reduce completion-token usage in this sample. Summary
generation consumed 10,141 completion tokens, and the compacted trajectory also
used more action steps. Nevertheless, the repeated savings in input context
were large enough to lower combined token usage overall.

## Tradeoffs

Compaction bounds active context, reduces repeated input cost, and lowers the
risk that long tool transcripts crowd the task and recent evidence out of the
model's context window. It can also remove distracting obsolete output.

The tradeoff is that summary calls add latency and completion-token cost. A
model-generated summary can omit a detail that later becomes important, so the
prompt must explicitly preserve objectives, constraints, edits, failures, test
results, blockers, and next actions. Retaining the most recent complete
assistant action with all linked tool observations provides a verbatim anchor
around the lossy working memory.
