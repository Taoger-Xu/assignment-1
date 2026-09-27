# Part 3 Observation Experiment

## Method

Each run used the repaired chess application, the same deterministic Black bot,
and a maximum of 200 agent steps. The only observation change was whether the
formatted chess state included the server-provided `legal_moves` list. A rejected
call is a `play_move` observation containing `<chess_error>`. The invalid-move
rate is rejected calls divided by total `play_move` calls.

## Results

| Model | Observation | `play_move` calls | Rejected as illegal | Invalid-move rate | Reached `game_over: true` | Outcome |
| --- | --- | ---: | ---: | ---: | --- | --- |
| DeepSeek Flash | Board/FEN only | 19 | 0 | 0.00% | Yes | White wins |
| DeepSeek Flash | Board/FEN + legal moves | 56 | 2 | 3.57% | Yes | Black wins |
| GPT-OSS-120B | Board/FEN only | Not run | Not run | Not available | Not run | Provider unavailable |
| GPT-OSS-120B | Board/FEN + legal moves | Not run | Not run | Not available | Not run | Provider unavailable |

## Comparison

In this single DeepSeek trial, omitting legal moves did not increase invalid
actions: the board-only run made no illegal calls and won in 19 calls. The run
with legal moves made two illegal calls (`d1c2` and `g1g2`) and lost after 56
calls. This does not establish that legal-move observations are harmful: each
condition has only one stochastic run, and the trajectories followed different
games. It does show that exposing a legal-move list does not guarantee the model
will copy from it correctly.

The requested GPT-OSS comparison could not be run with the configured API. Its
`/models` endpoint exposes only `deepseek-flash` and `deepseek-v4-pro`; requesting
`openai/gpt-oss-120b` would therefore not be a valid second-model experiment.
Complete those two rows with a key and OpenAI-compatible base URL from a provider
that serves `openai/gpt-oss-120b`, then run:

```bash
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal
```

The DeepSeek counts above were computed directly from the saved response tool
calls and their linked tool observations. The terminal status and outcome were
read from the corresponding result JSON files.
