# Agentic Evaluation

Razavi-Bench supports direct and file-based multimodal evaluation. Tasks with
figures must always include their PNG files; text-only runs are invalid for
figure-dependent questions.

| Mode | Input and execution |
| --- | --- |
| Direct multimodal QA | Send `instruction.md` and its figure PNGs directly to the answer model. |
| Agentic multimodal QA | Place the instruction and figures in `/app`; the agent writes `/app/answer.md`. |
| Agentic ngspice-sky130 | Use the same file workflow with ngspice, the bundled Sky130 assets, and the public skill. |

## Inputs And Scoring

Answer models and agents may receive only the public task instruction and its
figures. Do not expose `golden_solution.md`, `evaluation_rubric.md`, source
articles, judge data, private records, or the curated `netlists/` tree.

All modes are scored from the final answer against the same golden solution and
repository-level rubric. Agentic runs score only `/app/answer.md`; scratch
files, simulator decks, and logs are ignored.

## Agentic Multimodal

The task working directory is:

```text
/app/instruction.md
/app/figure-*.png
```

The required output is `/app/answer.md`. This mode is a harness-parity test and
should remain close to direct multimodal performance. Before attributing a
regression to the model, verify that the image reached the model, the agent was
asked to inspect it, and the final file was written and extracted correctly.

## Ngspice-Sky130

The simulator-assisted treatment additionally provides:

- `ngspice`;
- `simulator/ngspice-sky130/models` and `examples`;
- `agentic/skills/ngspice-sky130/SKILL.md`.

The skill is part of this treatment. It defines how to check topology, bias,
held-fixed conditions, and measurements before using simulation as evidence.
There is intentionally no per-task simulation routing table; every task gets
the same public tool and skill, and the agent decides whether simulation is
relevant.

The bundled Sky130 subset is not a full PDK or benchmark ground truth. Many
questions are qualitative or under-specified, so simulation supports rather
than replaces circuit reasoning. Harness examples are provided as Dockerfiles
under `agentic/harness/`.
