#!/usr/bin/env node
// Aggregate per-question data from models/*.json into questions/{question_id}.json
// Each output file: { question_id, question, figures, golden_solution, models: { model_key: { model info, rollouts: [ {rollout, answer, scores, active_score, tokens, cost} ] } } }
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const MODELS_DIR = path.join(ROOT, "docs/data/direct_qa/models");
const TASKS_FILE = path.join(ROOT, "data/tasks.jsonl");
const OUT_DIR = path.join(ROOT, "docs/data/direct_qa/questions");

// Load tasks for golden solution + instruction
const tasks = new Map();
fs.readFileSync(TASKS_FILE, "utf-8")
  .trim()
  .split(/\r?\n/)
  .filter(Boolean)
  .forEach((line) => {
    const row = JSON.parse(line);
    tasks.set(row.task_slug, row);
  });

const modelFiles = fs
  .readdirSync(MODELS_DIR)
  .filter((f) => f.endsWith(".json"));

const byQuestion = new Map();

modelFiles.forEach((file) => {
  const model = JSON.parse(
    fs.readFileSync(path.join(MODELS_DIR, file), "utf-8")
  );
  const modelKey = model.model_key;
  const entry = {
    model_key: modelKey,
    display_name: model.display_name,
    provider: model.provider,
    thinking_effort: model.thinking_effort,
    configuration_note: model.configuration_note || null,
    rollouts: {},
  };
  model.answers.forEach((a) => {
    const qid = a.question_id;
    if (!byQuestion.has(qid)) byQuestion.set(qid, { question_id: qid, models: {} });
    const q = byQuestion.get(qid);
    if (!q.question) {
      q.question = a.question;
      q.figures = a.figures || [];
      q.part = a.part;
      q.question_number = a.question_number;
    }
    if (!q.models[modelKey]) q.models[modelKey] = entry;
    // rollout keyed object
    entry.rollouts[a.rollout] = {
      rollout: a.rollout,
      answer: a.answer,
      scores: a.scores,
      active_score: a.active_score,
      tokens: a.tokens,
      model_call_count: a.model_call_count,
      attempt_count: a.attempt_count,
      source_experiment: a.source_experiment,
    };
  });
});

fs.mkdirSync(OUT_DIR, { recursive: true });
let written = 0;
for (const [qid, data] of byQuestion) {
  const task = tasks.get(qid);
  const out = {
    question_id: qid,
    part: data.part,
    question_number: data.question_number,
    question: data.question,
    figures: data.figures,
    instruction: task ? task.instruction : null,
    golden_solution: task ? task.golden_solution : null,
    models: data.models,
  };
  fs.writeFileSync(path.join(OUT_DIR, qid + ".json"), JSON.stringify(out));
  written++;
}
console.log(`Wrote ${written} question files to ${OUT_DIR}`);
console.log(`Sample: ${fs.readFileSync(path.join(OUT_DIR, "part1-001-double-length-and-width-mosfet-its-intrinsic.json"), "utf-8").slice(0, 200)}`);
