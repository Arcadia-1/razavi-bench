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
OpenRouter key runs the 50 tasks, grades them with the DeepSeek V4 Pro judge,
and builds the website data.

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
