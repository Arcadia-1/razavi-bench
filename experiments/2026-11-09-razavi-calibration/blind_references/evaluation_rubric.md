# Evaluation Rubric

The source Razavi articles provide AI responses, Razavi's comments, and 0-4
scores, but not a detailed per-point grading table. This file is an inferred
evaluation guide for re-scoring new model answers.

## Scale

| Score | Meaning | Criteria |
|---:|---|---|
| 4 | Correct | Correct conclusion and reasoning; topology, device roles, dominant mechanism, trend, and key assumptions are right. |
| 3 | Mostly correct | Main conclusion is right, with a minor omission, imprecision, or modeling flaw that does not change the result. |
| 2 | Partially correct | Identifies some relevant mechanism, but misses an important circuit detail, trend, or design consequence. |
| 1 | Mostly incorrect | Main conclusion is wrong, but the answer contains a small amount of relevant circuit understanding. |
| 0 | Incorrect or unusable | Fundamentally wrong, internally inconsistent, or based on a mistaken topology/device/connection. |

## Guidance

Evaluate against the task's `golden_solution.md`, prioritizing analog-circuit
reasoning over surface similarity to the original article answer. Reward correct
identification of device types, signal paths, feedback, loading, dominant
mechanisms, and valid boundary conditions. Penalize memorized formulas used
outside their assumptions, wrong topology recognition, missed shorts or
connections, and right final claims supported by misleading physical reasoning.

Do not treat Razavi's historical scores for article responses as hidden labels
for new model answers. They are examples used to infer this guide.

## Consistency Rules

Distinguish background recognition from answering the question. Correctly naming
a topology, writing a familiar input-match relation, identifying a device group,
or mentioning a real secondary effect is not enough for a high score if the
answer misses the dominant mechanism or design consequence asked by the task.

If the final conclusion contradicts the golden solution's central result, treat
the answer as mostly incorrect even if it contains some relevant circuit
background. Award partial credit only when the answer explicitly captures a
substantial part of the golden mechanism or tradeoff, not merely because it uses
reasonable analog vocabulary.

For trend and optimization questions, the direction of the trend and the design
conclusion are central. A one-sided answer that discusses a real limiting effect
but reaches the opposite design conclusion should be graded consistently as a
major miss, not as mostly correct.
