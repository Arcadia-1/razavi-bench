---
license: other
pretty_name: Razavi Bench
language:
  - en
task_categories:
  - question-answering
  - visual-question-answering
tags:
  - analog-design
  - circuit-design
  - benchmark
  - multimodal
  - llm-evaluation
  - electronic-design-automation
size_categories:
  - n<1K
configs:
  - config_name: tasks
    data_files:
      - split: train
        path: data/tasks.jsonl
---

<h1 align="center">Razavi-Bench</h1>

<p align="center">
  <a href="https://razavi-bench.tokenzhang.com"><strong>Visit our website</strong></a>
</p>

Razavi-Bench is an expert-curated benchmark for analog-design reasoning: 50
multimodal questions from Behzad Razavi's *Analog Design Experiments With AI*
(Part 1: 30 questions, Part 2: 20), each with a figure where needed and a
curated golden answer under `tasks/`. The leaderboard, every model answer, and
the judge's scores are on the website.

To evaluate a model yourself, see [`tools/README.md`](tools/README.md): one
OpenRouter key runs the 50 tasks, grades them with the GPT-6 Luna judge at
maximum reasoning effort, and builds the website data.

## What a model receives

Each answer comes from one request holding a single user message and no system
prompt. The message has two parts:

1. the task's `prompt` text in `data/tasks.jsonl`. This is the "## Question"
   section of `tasks/<task>/instruction.md` and nothing else: no title, headings,
   figure numbers or subfigure labels;
2. the task's figure (`figures`) as a PNG image after the text. 46 tasks have one
   figure and 4 have none. Each figure shows only the part of the circuit that its
   question asks about.

The leaderboard runs every model at its highest reasoning effort, with `max_tokens`
at the model's own output limit. An answer cut off at that limit is re-run; one cut
off on every attempt is graded as returned. Every task is answered in three
independent trials, with no tools, web access, reference answers or earlier
feedback. GPT-6 Luna at maximum reasoning effort grades each answer from 0 to 4
against the task's `golden_solution` and [`evaluation_rubric.md`](evaluation_rubric.md).

`tools/direct_qa_openrouter.py` sends exactly these messages. The leaderboard's own
runs are in [`experiments/2026-11-09-question-only-rerun`](experiments/2026-11-09-question-only-rerun).

### `data/tasks.jsonl`

| Field | Content |
| --- | --- |
| `task_slug`, `part`, `question_number`, `task_path` | Task identity and folder |
| `prompt` | The text sent to the model |
| `figures` | The images sent after the text, in order |
| `instruction` | The whole `instruction.md`, for reference; not sent |
| `golden_solution` | The reference answer the judge grades against; never sent |

`tools/export_tasks.py` rebuilds the file from `tasks/`, and refuses a prompt that
names its task or cites a figure number.

## Citation

```bibtex
@misc{zhang2026razavibench,
  title        = {Razavi-Bench: An Expert-Curated Benchmark for Analog-Design Reasoning},
  author       = {Zhishuai Zhang},
  year         = {2026},
  howpublished = {\url{https://github.com/Arcadia-1/razavi-bench}},
  url          = {https://razavi-bench.tokenzhang.com/},
  note         = {Benchmark repository}
}
```

## License

Software code is licensed under Apache-2.0. Benchmark materials (questions,
figures, golden solutions, rubrics, model outputs, and scores) adapt Behzad
Razavi's articles with his permission and are available for viewing, citation,
non-commercial research, and local evaluation only; they may not be
redistributed, used for training, or incorporated into other benchmarks or
datasets without prior written permission. See [`LICENSE`](LICENSE) for the
full terms.

## References

- B. Razavi, "Analog Design Experiments With AI—Part 1 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 17, no. 4, pp. 11-15, Fall 2025.
- B. Razavi, "Analog Design Experiments With AI—Part 2 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 18, no. 2, pp. 8-13, Spring 2026.
