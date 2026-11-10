#!/usr/bin/env python3
"""Write prompts.html: every question exactly as this rerun sends it.

The text and images come from run.build(), the function that builds each request,
and the images are embedded byte for byte as sent. Each question also shows how
many requests logged in runs/*/requests.jsonl carry exactly this content and how
many carried an older figure (those answers are superseded and re-run).
"""

from __future__ import annotations

import html
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

CROPPED = {"part1-014", "part1-015", "part2-013", "part2-014", "part2-015", "part2-017"}

CSS = """
body { font-family: -apple-system, "Helvetica Neue", "PingFang SC", sans-serif; max-width: 1000px; margin: 2em auto; padding: 0 1em; color: #1b1b1b; background: #fafafa; }
h1 { font-size: 1.5em; } h2 { font-size: 1.15em; margin: 0; }
table { border-collapse: collapse; font-size: 0.9em; } td, th { border: 1px solid #ccc; padding: 4px 8px; text-align: left; }
.card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1em 1.2em; margin: 1.2em 0; }
.meta { color: #777; font-size: 0.85em; }
.label { font-size: 0.8em; color: #555; margin: 0.8em 0 0.3em; text-transform: uppercase; letter-spacing: 0.04em; }
.sent { white-space: pre-wrap; border: 2px solid #2a6fdb; border-radius: 6px; padding: 0.7em 0.9em; background: #f3f7ff; font-size: 1em; line-height: 1.5; }
.img { border: 2px solid #2a6fdb; border-radius: 6px; padding: 6px; display: inline-block; background: white; max-width: 100%; }
.img img { max-width: 100%; display: block; }
.badge { display: inline-block; font-size: 0.75em; padding: 1px 7px; border-radius: 10px; margin-left: 6px; vertical-align: middle; }
.ok { background: #e3f4e6; color: #1d6b2c; } .warn { background: #fff1d6; color: #8a5a00; } .bad { background: #fde2e2; color: #9b1c1c; }
details { margin-top: 0.8em; } summary { cursor: pointer; color: #555; font-size: 0.85em; }
pre { font-size: 0.78em; background: #f4f4f4; padding: 0.6em; overflow-x: auto; }
nav a { margin-right: 0.6em; font-size: 0.85em; }
"""


def logged_requests():
    rows = []
    for path in sorted((HERE / "runs").glob("*/requests.jsonl")):
        rows += [json.loads(line) for line in path.read_text().splitlines()]
    return rows


def main() -> None:
    tasks = run.probe.load_tasks(run.REPO)
    requests = logged_requests()
    shapes = Counter((len(r["body"]["messages"]), r["body"]["messages"][0]["role"]) for r in requests)
    sent = {}
    for t in tasks:
        _, logged = run.build(t)
        sent[t["task_slug"]] = json.dumps(logged, sort_keys=True)
    match, older = Counter(), Counter()
    for r in requests:
        same = json.dumps(r["body"]["messages"][0]["content"], sort_keys=True) == sent[r["task_slug"]]
        (match if same else older)[r["task_slug"]] += 1

    out = [f"<!doctype html><meta charset='utf-8'><title>Razavi-Bench: what each model receives</title><style>{CSS}</style>",
           "<h1>模型实际收到的题面（question-only rerun）</h1>",
           "<p>每个请求只有<b>一条 user 消息</b>：先是下面蓝框里的文字，后面紧跟蓝框里的图片（原字节，base64 PNG）。"
           "没有 system prompt、没有标题、没有小节标题、没有图片链接。蓝框以外的内容（题号、文件名、尺寸、哈希）是本页的注释，不发给模型。</p>",
           f"<p class='meta'>已检查 runs/ 里记录的全部 {len(requests)} 个请求的消息结构："
           + "，".join(f"{n} 条消息、角色 {role}：{c} 个" for (n, role), c in shapes.items()) + "。</p>",
           "<table><tr><th>条目</th><th>OpenRouter 模型</th><th>推理强度</th><th>temperature</th><th>max_tokens</th></tr>"]
    for name, (model, effort, temperature, max_tokens) in run.ENTRIES.items():
        out.append(f"<tr><td>{html.escape(name)}</td><td><code>{model}</code></td><td>{effort or '无此设置'}</td>"
                   f"<td>{'服务商默认' if temperature is None else temperature}</td><td>{max_tokens:,}</td></tr>")
    out.append("</table><nav><p>")
    for t in tasks:
        slug = t["task_slug"]
        out.append(f"<a href='#{slug[:9]}'>{'P1' if slug.startswith('part1') else 'P2'} Q{int(slug[6:9])}</a>")
    out.append("</p></nav>")

    for t in tasks:
        slug = t["task_slug"]
        content, logged = run.build(t)
        title = f"{'Part 1' if slug.startswith('part1') else 'Part 2'} Q{int(slug[6:9])}"
        badges = f"<span class='badge ok'>本轮已发送 {match[slug]} 次，与此完全一致</span>"
        if older[slug]:
            badges += f"<span class='badge bad'>{older[slug]} 次用的是旧题面或旧图，已作废、会重跑</span>"
        if slug[:9] in CROPPED:
            badges += "<span class='badge warn'>图已裁剪、去掉子图标号</span>"
        out.append(f"<div class='card' id='{slug[:9]}'><h2>{title}{badges}</h2>"
                   f"<div class='meta'>内部标识 {slug}（不发给模型）</div>"
                   f"<div class='label'>发送的文字</div><div class='sent'>{html.escape(content[0]['text'])}</div>")
        images = content[1:]
        if images:
            out.append(f"<div class='label'>发送的图片（{len(images)} 张）</div>")
            for part, info in zip(images, logged[1:]):
                image = info["image"]
                out.append(f"<div class='img'><img src='{part['image_url']['url']}' alt='figure'></div>"
                           f"<div class='meta'>{image['file']} · {image['width']}×{image['height']} px · "
                           f"{image['bytes']:,} bytes · sha256 {image['sha256'][:16]}…</div>")
        else:
            out.append("<div class='label'>发送的图片</div><div class='meta'>无（这道题没有图）</div>")
        shown = json.loads(json.dumps(content))
        for part in shown[1:]:
            url = part["image_url"]["url"]
            part["image_url"]["url"] = url[:40] + f"…（共 {len(url):,} 个字符）"
        out.append("<details><summary>完整的 messages 字段（图片数据已截断显示）</summary><pre>"
                   + html.escape(json.dumps([{"role": "user", "content": shown}], indent=1, ensure_ascii=False))
                   + "</pre></details></div>")

    (HERE / "prompts.html").write_text("\n".join(out))
    print(f"prompts.html: {len(tasks)} questions; requests matching {sum(match.values())}, older figure {sum(older.values())}")


if __name__ == "__main__":
    main()
