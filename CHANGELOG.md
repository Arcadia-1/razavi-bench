# Changelog

Notable changes to Razavi-Bench, newest first, by commit date.

## 2026-11-10

1. Reran every leaderboard entry with only the question text and its figure, at each model's highest reasoning effort and max_tokens at its output limit; scores fell 6.0 points on average.
2. Replaced the website's data with the rerun: 71 entries, adding Claude Fable 5.2 and removing Claude Opus 5 at high, xhigh and medium effort, GPT-6 Sol (thinking high), MiniMax-01, Claude Sonnet 4 and Doubao Seed 2.1 Pro.
3. Restored Part 2 Q6 and Q12 to Razavi's wording and gave the Q6 reference partial-credit tiers.
4. Priced the self-hosted entries (Qwen 3.8 27B, Qwen 3.5 9B, GLM 5.3 Flash) at OpenRouter's rates, and linked this changelog from every page's footer.
5. Added each task's exact prompt to `data/tasks.jsonl` and switched the runners in `tools/` to send only it.
6. Updated the Hugging Face dataset (Arcadia-2026/razavi-bench) to the current tasks, figures, references and prompts, and removed its old June experiment files, docs and article PDFs.
7. Replaced MiniMax M3's entry with a run through MiniMax's own API (69.2%, against 64.3% through OpenRouter) and added MiniMax M3.1 Flash (72.7%).
8. Priced every model at OpenRouter's list price on 2026-11-10 (`tools/sync_openrouter_prices.py`); 23 models' costs changed.
9. Agentic (Harbor) tasks now give the agent only the question, with no title or figure numbers, and name the figure `figure-1.png`.
10. Added Gemini 4 Carbon (released 2026-11-10), now first at 98.3%.

## 2026-11-09

1. Corrected 34 more reference answers against Razavi's own scores (13, then 21) and re-graded the affected answers.
2. Removed figure numbers, subfigure labels and answer hints from the questions; figures that showed more than a question asks about were split or cropped.
3. Calibrated the judge against Razavi's scores of the article's answers: 48 of 50 questions match.

## 2026-11-08

1. Revised six reference answers (Part 1 Q2 and Q22, and four that simulation contradicts) and re-graded them, along with the reasoning-trace probe.

## 2026-11-07

1. Published self-hosted Qwen 3.5 9B and reran Qwen 3.8 27B from its BF16 checkpoint on B200 GPUs.

## 2026-11-05

1. Added a probe that records reasoning traces and answer times.
2. Recounted Claude Fable 5's tokens after its tool-free reruns.

## 2026-11-04

1. Published Hy4.

## 2026-11-03

1. Reran Claude Fable 5's eleven answers that had used tools, without tools.
2. Kept Muse Code runs on Meta's API despite a local endpoint override; renamed GPT 5.6 Sol to GPT-5.6 Sol.

## 2026-11-02

1. Filled the release timeline with older models: six from late 2025, four late-2024 vision models, and GPT-4o's May and August 2024 snapshots.
2. Added GPT-5.3 at xhigh effort and reran GPT-5, Gemini 2.5 Pro and Gemini 3.5 Flash at their top effort.
3. Recorded an agentic ngspice-sky130 run through Harbor.

## 2026-10-30

1. Built mini-swe-agent and Claude Code into the Harbor task images; all agentic runs now go through Harbor.
2. Recorded the Harbor parity run of DeepSeek V4.1 Flash 1017 (87.83%, against 87.50% with the standalone runner).

## 2026-10-28

1. Built Codex and Gemini CLI into the Harbor task images.

## 2026-10-27

1. Added agentic runs: the 50 tasks export as Harbor tasks, run by an image-aware mini-swe-agent, with golden solutions kept out of the agent's container.

## 2026-10-26

1. Graded every published answer with GPT-6 Luna at maximum reasoning effort, recording the judge's token usage.
2. Published Kimi 3.1 Pro and added Moonshot and MiniMax providers to the Direct QA runner, with MiniMax requests streamed.
3. Corrected the note on why Nemotron 3.5 Super VL scores low and stopped the homepage flashing a stale model count.

## 2026-10-20

1. Published Nemotron 3.5 Super VL and added NVIDIA to the release timeline.

## 2026-10-19

1. Added an NVIDIA provider to the runner with retries on dropped connections; renamed the September entry DeepSeek V4.1 Flash 0910.

## 2026-10-18

1. Published DeepSeek V4.1 Flash 1017 and let the runner call the DeepSeek API directly.

## 2026-10-14

1. Published Gemini 4 Argon, and Muse Wonder Full 1.0 through a new Muse Code CLI runner.
2. Labelled a newest-month frontier model on the right of the release timeline.

## 2026-10-08

1. Published Muse Spark 1.3; the runner now checks the requested effort against the model's listed efforts.
2. Corrected Mistral Large 4's effort label and showed each model's effort on the resource-usage chart.
3. Added Show all to the timeline legend and trimmed the README to a pointer to the website.

## 2026-10-07

1. Published Mistral Large 4 and Claude Haiku 5.5.
2. Added a generic builder for the model files; answers cut off at max_tokens are retried and every attempt is billed.
3. The site now prefers its own leaderboard data over the raw GitHub copy.

## 2026-10-02

1. Published Gemini 3.8 Flash and added a standalone OpenRouter Direct QA runner.

## 2026-10-01

1. Published GPT-6.1 Sol and added OpenRouter reasoning control to the judge tool.

## 2026-09-29

1. Published GPT-6 Sol (thinking high), Mistral Large 2512, Doubao Seed 2.1 Pro, GLM 5.3 Flash and Mimo 2.6 Pro.
2. Dropped version dates from display names; the provider timeline got official brand colours and a Clear all control.
3. Priced GLM 5.3 Flash from Z.ai's published API rates.

## 2026-09-28

1. Published Mistral Medium 3.5 and Grok 4.7.

## 2026-09-27

1. Published DeepSeek V4.1 Flash.

## 2026-09-26

1. Redesigned the homepage after Analog Design Bench: a masonry task grid with figures, tasks numbered 1-50, a tighter hero and matching page width.
2. Added a model page with every task's answers in Part 1 and Part 2 columns.
3. Published GPT-6 Sol.
4. Rebuilt the analytics page with visitor counts and a request-location map served by the worker.

## 2026-09-25

1. Published Claude Opus 5.5 and Claude Fable 5.1.
2. Reworked the release-date chart: points grouped by month, one spare month, labelled frontier models.
3. Restyled the site to match Analog Design Bench: green accents, an R logo and a pinned nav bar.

## 2026-09-18

1. Removed the obsolete dashboard pages.

## 2026-09-14

1. Updated the author name.
