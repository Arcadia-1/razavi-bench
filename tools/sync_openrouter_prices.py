#!/usr/bin/env python3
"""Set every published model's price in docs/assets/pricing.js to OpenRouter's current list price.

Each model file's `api_model` names the OpenRouter model (self-hosted checkpoints and runs through
a vendor's own API map to the same model on OpenRouter, via ALIASES). Prices are per 1M tokens:
[input, output, cached input]; a model with no listed cache-read price bills cached input at the
input price. The PRICE block is rewritten one entry per line, in model-key order, and the date of
the prices is recorded in its comment. Refuses to write if any published model is not on OpenRouter.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICING = ROOT / "docs/assets/pricing.js"
MODELS = ROOT / "docs/data/direct_qa/models"
ALIASES = {
    "MiniMax-M3": "minimax/minimax-m3",
    "MiniMax-M3.1-Flash": "minimax/minimax-m3.1-flash",
    "Qwen/Qwen3.8-27B": "qwen/qwen3.8-27b",
    "Qwen/Qwen3.5-9B": "qwen/qwen3.5-9b",
    "zai-org/GLM-5.3-Flash-BF16": "z-ai/glm-5.3-flash",
}


def per_million(value: str | None) -> float:
    return round(float(value or 0) * 1e6, 6)


def main() -> None:
    listed = {m["id"]: m["pricing"] for m in json.load(urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60))["data"]}
    prices, missing = {}, []
    for path in sorted(MODELS.glob("*.json")):
        model = json.loads(path.read_text())
        api = model["answers"][0]["configuration"]["api_model"]
        pricing = listed.get(ALIASES.get(api, api))
        if pricing is None:
            missing.append((model["model_key"], api))
            continue
        price_in, price_out = per_million(pricing["prompt"]), per_million(pricing["completion"])
        cached = per_million(pricing.get("input_cache_read")) or price_in
        prices[model["model_key"]] = [price_in, price_out, cached]
    if missing:
        raise SystemExit(f"not on OpenRouter: {missing}")
    text = PRICING.read_text()
    start, end = text.index("var PRICE={"), text.index("};", text.index("var PRICE={")) + 2
    body = ",\n".join(f"  {key}:[{','.join(f'{v:g}' for v in value)}]" for key, value in prices.items())
    text = text[:start] + "var PRICE={\n" + body + "\n};" + text[end:]
    text = re.sub(r"// API prices per 1M tokens: \[input, output, cached\]\..*\n",
                  f"// API prices per 1M tokens: [input, output, cached], OpenRouter's list prices on {date.today()}"
                  " (tools/sync_openrouter_prices.py).\n", text)
    PRICING.write_text(text)
    print(f"wrote {len(prices)} prices to {PRICING.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
