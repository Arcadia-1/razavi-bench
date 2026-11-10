#!/usr/bin/env python3
"""Publish the question-only rerun as the website's Direct QA data, replacing every published run.

For each entry in rerun_scores.csv this writes docs/data/direct_qa/models/<model_key>.json with
tools/build_model_json.py's build(): the answer collect_scores.py selects for each (task, rollout),
GPT-6 Luna's score of that exact answer against the current golden solution, and token usage from
the traces. A slot's billed tokens sum every attempt that used the same configuration (model,
effort, max_tokens, temperature, request options, question text and figures), so retries of
answers cut off at max_tokens count; the selected response's own usage is kept beside them.

It also removes the dropped entries (collect_scores.DROPPED) from the model files, index.json and
model_release_dates.csv, adds the new entries (collect_scores.NEW_ENTRIES), and records each entry's
rerun effort in model_release_dates.csv. Then run tools/apply_active_judge.py,
tools/aggregate_questions.js, tools/build_release_date_index.py and the plotting tools.
The replaced files stay in git history.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "docs/data/direct_qa"
EXPERIMENT = HERE.name
JUDGE = "gpt_6_luna_max"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cs = load("collect_scores", HERE / "collect_scores.py")
bmj = load("build_model_json", REPO / "tools/build_model_json.py")

# Self-hosted checkpoints (route selfhosted_vllm_chat_completions): how each was served and set.
SELF_HOSTED = {
    "qwen_38_27b": ("Self-hosted official BF16 checkpoint (Qwen/Qwen3.8-27B, revision 8c0b3d30) on vLLM 0.33.0 with the "
                    "qwen3 reasoning parser. Qwen 3.8 27B answered the 50 tasks in three rollouts at reasoning effort "
                    "xhigh, the highest its chat template accepts, with Qwen's recommended thinking-mode sampling "
                    "(temperature 1.0, top_p 0.95)"),
    "qwen_35_9b": ("Self-hosted official BF16 checkpoint (Qwen/Qwen3.5-9B, revision c2022362) on vLLM 0.33.0 with the "
                   "qwen3 reasoning parser. Qwen 3.5 9B answered the 50 tasks in three rollouts with thinking on, its "
                   "only reasoning setting, with Qwen's recommended thinking-mode sampling (temperature 1.0, top_p 0.95)"),
    "glm_5_3_flash_260828_max": ("Self-hosted official BF16 weights (zai-org/GLM-5.3-Flash-BF16, revision f9fed3bb) on "
                                 "vLLM 0.33.0. GLM 5.3 Flash answered the 50 tasks in three rollouts at reasoning effort "
                                 "max, its chat template's default and highest level, with the sampling of its "
                                 "generation_config (temperature 1.0, top_p 0.95)"),
}
# Effort shown on the site where the trace records the server default rather than its level.
EFFORT_SHOWN = {"glm_5_3_flash_260828_max": "max"}
# Models whose reasoning is a switch rather than effort levels.
THINKING_ONLY = {"kimi_k27"}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prices() -> dict[str, list[float]]:
    text = (REPO / "docs/assets/pricing.js").read_text()
    body = text.split("var PRICE={", 1)[1].split("};", 1)[0]
    return {k: [float(x) for x in v.split(",")] for k, v in re.findall(r"(\w+):\[([^\]]+)\]", body)}


def selected_answers() -> dict[tuple[str, str, int], dict]:
    """collect_scores.collect()'s selection, keeping the answer rows."""
    answers = {}
    for spec in cs.ANSWERS:
        candidates = [HERE / p for p in spec.split("|") if (HERE / p).exists()]
        path = max(candidates, key=lambda c: len(cs.read(c)), default=None)
        if path is None:
            continue
        for r in cs.read(path):
            model = cs.RELABEL.get(r["model_name"], r["model_name"])
            if model == "glm_5_3_flash_260828_max" and not path.name.startswith("answers_selfhosted"):
                continue
            answers[(model, r["task_slug"], r["rollout"])] = {**r, "_selfhosted": path.name.startswith("answers_selfhosted")}
    return answers


def score_rows(golden: dict[str, str]) -> tuple[dict, dict]:
    by_model, any_model = {}, {}
    for name in cs.SCORES:
        for s in cs.read(HERE / name):
            if golden[s["task_slug"]] != s["golden_solution_sha256"]:
                continue
            model = cs.RELABEL.get(s["answer_metadata"]["model_name"], s["answer_metadata"]["model_name"])
            by_model[(model, s["answer_sha256"], s["task_slug"])] = s
            any_model[(s["answer_sha256"], s["task_slug"])] = s
    return by_model, any_model


def traces() -> dict[tuple[str, str, int], list[dict]]:
    slots = defaultdict(list)
    for path in sorted(HERE.rglob("traces.jsonl")):
        if "discarded" in path.parts:
            continue
        for row in cs.read(path):
            row["_selfhosted"] = "runs_selfhosted" in path.parts
            model = cs.RELABEL.get(row["model_key"], row["model_key"])
            slots[(model, row["task_slug"], row["rollout"])].append(row)
    return slots


def configuration(row: dict) -> tuple:
    return (row.get("model"), row.get("effort"), row.get("max_tokens"), row.get("temperature"),
            json.dumps(row.get("request_options"), sort_keys=True), json.dumps(row.get("settings"), sort_keys=True),
            row.get("question"), tuple(f["sha256"] for f in row.get("figures") or []))


def usage_of(rows: list[dict]) -> tuple[dict, int]:
    """Billed tokens over every attempt that returned usage, and the number of such attempts."""
    records = []
    for row in rows:
        attempts = row.get("attempts") or []
        usages = [a["usage"] for a in attempts if a.get("usage")] if attempts else [row.get("usage") or {}]
        records += [bmj.usage_record(u) for u in usages]
    if not records:
        records = [bmj.usage_record({})]
    return (bmj.sum_usage(records) if len(records) > 1 else records[0]), len(records)


def effort_phrase(key: str, effort: str) -> str:
    if key in THINKING_ONLY:
        return "with thinking on (the model has no effort levels)"
    if effort == "default":
        return "without reasoning (the model has no reasoning setting)"
    if effort == "max":
        return "at maximum reasoning effort"
    return f"at reasoning effort {effort}, the highest it offers"


def note(key: str, name: str, rows: list[dict], effort: str, looped: int, price: list[float] | None) -> str:
    row = rows[0]
    if key in SELF_HOSTED:
        text = SELF_HOSTED[key] + ", and no max_tokens, so the server allowed the 262,144-token context less the prompt."
    else:
        settings = [f"max_tokens to {row['max_tokens']:,}, the model's output limit"]
        if row.get("temperature") is not None:
            settings.append(f"temperature to {row['temperature']:g}")
        top_p = (row.get("request_options") or {}).get("top_p")
        if top_p is not None:
            settings.append(f"top_p to {top_p:g}, as its model card recommends")
        listed = settings[0] if len(settings) == 1 else ", ".join(settings[:-1]) + " and " + settings[-1]
        text = (f"{name} answered the 50 tasks in three rollouts through OpenRouter's chat completions route "
                f"({row['model']}) {effort_phrase(key, effort)}. Requests set {listed}.")
    text += (" Each request was one user message holding only the question text and its figure: no title, "
             "headings or system prompt. Answers cut off at the output limit were re-run; every attempt is counted in "
             "tokens and cost.")
    if looped:
        text += (f" In {looped} slot{'s' if looped > 1 else ''} the model reached its output limit on every attempt; "
                 f"{'those answers are' if looped > 1 else 'that answer is'} graded as returned.")
    text += " Answers were graded by GPT-6 Luna at maximum reasoning effort."
    if price:
        text += ((" The checkpoint is self-hosted; like every other entry, its cost" if key in SELF_HOSTED else " Cost")
                 + f" uses OpenRouter's published {name} API price (${price[0]:.2f} input, ${price[2]:g} cached input, "
                 f"${price[1]:.2f} output per 1M tokens).")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="check every entry without writing")
    args = parser.parse_args()

    rows = cs.collect()
    incomplete = [r["name"] for r in rows if r["rerun"] == ""]
    if incomplete:
        raise SystemExit(f"incomplete entries: {incomplete}")
    golden = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO / "tasks").glob("*/golden_solution.md")}
    tasks = {t["task_slug"]: t for t in cs.read(REPO / "data/tasks.jsonl")}
    answers = selected_answers()
    by_model, any_model = score_rows(golden)
    slots = traces()
    price = prices()
    index = json.loads((DATA / "index.json").read_text())
    names = {m["model_key"]: (m["display_name"], m.get("provider")) for m in index["models"]}
    names.update({k: (v[0], v[1]) for k, v in cs.NEW_ENTRIES.items()})

    built = {}
    for entry in rows:
        key = entry["model_key"]
        name, provider = names[key]
        chosen, scores, tokens, selected_rows = [], {}, {}, []
        looped = 0
        for slug in sorted(tasks):
            for rollout in (1, 2, 3):
                answer = answers[(key, slug, rollout)]
                digest = sha(answer["answer"])
                score = by_model.get((key, digest, slug)) or any_model.get((digest, slug))
                matches = [r for r in slots[(key, slug, rollout)]  # same text can come from another run
                           if sha(r.get("answer") or "") == digest and r["_selfhosted"] == answer["_selfhosted"]]
                if score is None or not matches:
                    raise SystemExit(f"{key} {slug} r{rollout}: score={score is not None} trace={bool(matches)}")
                selected = matches[-1]
                same = [r for r in slots[(key, slug, rollout)] if configuration(r) == configuration(selected)]
                billed, count = usage_of(same)
                tokens[f"{rollout}:{slug}"] = (billed, bmj.usage_record(selected.get("usage") or {}), count)
                scores[(slug, rollout)] = score
                looped += selected.get("finish_reason") == "length"
                selected_rows.append(selected)
                task = tasks[slug]
                chosen.append({"task_slug": slug, "task_path": task["task_path"], "rollout": rollout,
                               "question": task["instruction"], "figures": task.get("figures") or [],
                               "answer": answer["answer"], "model_call_attempts": count})
        efforts = {r["effort"] for r in selected_rows}
        models = {r["model"] for r in selected_rows}
        if len(efforts) != 1 or len(models) != 1:
            raise SystemExit(f"{key}: mixed configuration efforts={efforts} models={models}")
        effort = EFFORT_SHOWN.get(key, efforts.pop())
        route = "selfhosted_vllm_chat_completions" if selected_rows[0]["_selfhosted"] else "openrouter_chat_completions"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "answers.jsonl"
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in chosen), encoding="utf-8")
            bmj.load_scores = lambda _path, scores=scores: scores
            bmj.load_tokens = lambda _args, tokens=tokens: tokens
            model = bmj.build(argparse.Namespace(
                model_key=key, display_name=name, provider=provider, effort=effort, api_model=models.pop(), route=route,
                source_experiment=EXPERIMENT, judge_key=JUDGE, answers=[path], scores=None, tokens=None, raw_log=None,
                unanswered=[],
                configuration_note=note(key, name, selected_rows, effort, looped,
                                        # pricing.js falls back to a key that prefixes the model key
                                        price.get(key) or next((v for k, v in price.items() if key.startswith(k)), None))))
        for a in model["answers"]:
            a["scores"][JUDGE]["judge_model"] = "openai/gpt-6-luna"
        percent = model["summary"]["scores"]["overall"][JUDGE]["score_percent"]
        assert abs(percent - float(entry["rerun"])) < 0.01, (key, percent, entry["rerun"])
        built[key] = model
        print(f"{key:32s} {percent:6.2f}  effort={effort:8s} looped={looped} route={route}")

    print(f"{len(built)} entries built")
    if args.dry_run:
        return 0
    for key, model in built.items():
        (DATA / "models" / f"{key}.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in cs.DROPPED:
        (DATA / "models" / f"{key}.json").unlink(missing_ok=True)
    index["models"] = [m for m in index["models"] if m["model_key"] not in cs.DROPPED]
    (DATA / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    dates_path = DATA / "model_release_dates.csv"
    with dates_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields, dates = reader.fieldnames, [r for r in reader if r["model_key"] not in cs.DROPPED]
    for r in dates:
        if r["model_key"] in built:
            r["thinking_effort"] = built[r["model_key"]]["thinking_effort"]
    for key, (name, provider, day) in cs.NEW_ENTRIES.items():
        if not any(r["model_key"] == key for r in dates):
            api_model = built[key]["answers"][0]["configuration"]["api_model"]
            dates.append({"model_key": key, "display_name": name, "provider": provider,
                          "thinking_effort": built[key]["thinking_effort"], "source_model_id": f"openrouter:{api_model}",
                          "release_date": day, "date_basis": "openrouter_first_listed",
                          "source_url": f"https://openrouter.ai/{api_model}", "notes": ""})
    with dates_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dates)
    print("wrote model files, index.json and model_release_dates.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
