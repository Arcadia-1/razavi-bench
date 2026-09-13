#!/usr/bin/env python3
import argparse
import asyncio

from judge_common import add_common_args, post_chat, run_judge


API_URL = "https://api.minimaxi.com/v1/chat/completions"


def minimax_chat(
    api_key: str,
    model: str,
    messages: list[dict],
    timeout: int,
    max_tokens: int,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    if model == "MiniMax-M3":
        payload["thinking"] = {"type": "disabled"}
    body = post_chat(api_key, API_URL, payload, timeout)
    return body["choices"][0]["message"].get("content") or ""


def main() -> None:
    parser = argparse.ArgumentParser()
    add_common_args(
        parser,
        default_model="MiniMax-M3",
        default_output_name="minimax-m3",
        default_max_tokens=8192,
    )
    args = parser.parse_args()

    def chat(api_key: str, model: str, messages: list[dict], timeout: int) -> str:
        return minimax_chat(api_key, model, messages, timeout, args.max_tokens)

    asyncio.run(run_judge(args, chat, api_env="MINIMAX_API_KEY"))


if __name__ == "__main__":
    main()
