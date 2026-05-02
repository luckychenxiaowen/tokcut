import asyncio
import httpx
import json
import time
import os
from typing import Dict, List

MODELS = {
    "deepseek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "api_key": os.getenv("DEEPSEEK_API_KEY", "your-key"),
        "model": "deepseek-chat"
    },
    "glm": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key": os.getenv("GLM_API_KEY", "your-key"),
        "model": "glm-4"
    },
    "minimax": {
        "url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "api_key": os.getenv("MINIMAX_API_KEY", "your-key"),
        "model": "abab5.5-chat"
    },
    "hy": {
        "url": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
        "api_key": os.getenv("HUNYUAN_API_KEY", "your-key"),
        "model": "hunyuan-lite"
    },
    "kimi": {
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "api_key": os.getenv("MOONSHOT_API_KEY", "your-key"),
        "model": "moonshot-v1-8k"
    }
}

TASKS = [
    {
        "category": "代码修复",
        "prompt": "我的 React 组件每次父组件更新时都重新渲染，尽管我用了 memo。请说明可能的原因和修复方法。"
    },
    {
        "category": "文本总结",
        "prompt": "请用精简的语言总结以下内容：'今天上午我们召开了产品规划会议，讨论了A、B、C三个功能的优先级，最终决定先做A功能，因为它对用户增长最有利。下午又和技术团队确认了排期，预计两周内完成。'"
    },
    {
        "category": "知识问答",
        "prompt": "什么是大语言模型中的 RLHF？"
    },
    {
        "category": "翻译任务",
        "prompt": "将以下英文翻译成中文：'The rapid advancement of artificial intelligence has transformed many industries, but it also raises ethical concerns about privacy and employment.'"
    },
    {
        "category": "对话任务",
        "prompt": "作为一个客服，用户说：我的订单还没发货，已经三天了，能帮我查一下吗？请给出一个专业的回复。"
    },
]

PROXY_URL = "http://localhost:8800/v1/chat/completions"


async def call_model(client: httpx.AsyncClient, provider: Dict, prompt: str, use_tokcut: bool):
    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json"
    }
    body = {
        "model": provider["model"],
        "messages": [{"role": "user", "content": prompt}]
    }
    if use_tokcut:
        url = PROXY_URL
        headers["X-Provider-URL"] = provider["url"]
    else:
        url = provider["url"]

    start = time.time()
    resp = await client.post(url, json=body, headers=headers, timeout=120)
    elapsed = time.time() - start
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    tokcut_info = data.get("tokcut", {})
    return {
        "content": content,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "tokcut_input_before": tokcut_info.get("input_tokens_before"),
        "tokcut_input_after": tokcut_info.get("input_tokens_after_compression"),
        "tokcut_output_approx": tokcut_info.get("output_tokens_approx"),
        "elapsed": elapsed
    }


async def run_benchmarks():
    async with httpx.AsyncClient() as client:
        results = {}
        for name, provider in MODELS.items():
            print(f"\n=== Testing {name} ===")
            results[name] = []
            for task in TASKS:
                print(f"  Task: {task['category']}")
                res_without = await call_model(client, provider, task["prompt"], False)
                res_with = await call_model(client, provider, task["prompt"], True)
                results[name].append({
                    "task": task["category"],
                    "without": res_without,
                    "with": res_with
                })
                if res_without["total_tokens"] and res_with["total_tokens"]:
                    savings = res_without["total_tokens"] - res_with["total_tokens"]
                    rate = savings / res_without["total_tokens"] * 100
                    print(
                        f"    without: {res_without['total_tokens']} tokens, "
                        f"with: {res_with['total_tokens']} tokens, "
                        f"saved: {savings} ({rate:.1f}%)"
                    )
                else:
                    print("    Token data incomplete")

    save_report(results)


def save_report(results):
    report = "# Token 节省效果对比报告\n\n"
    for model, tasks in results.items():
        report += f"## {model}\n"
        total_without = 0
        total_with = 0
        for t in tasks:
            wout = t["without"]["total_tokens"] or 0
            w = t["with"]["total_tokens"] or 0
            total_without += wout
            total_with += w
            rate = ((wout - w) / wout * 100) if wout else 0
            report += (
                f"- {t['task']}: 未使用 {wout} → 使用 {w} "
                f"(节省 {wout - w}, {rate:.1f}%)\n"
            )
        total_saving = total_without - total_with
        total_rate = (total_saving / total_without * 100) if total_without else 0
        report += (
            f"\n**总计**: {total_without} → {total_with} "
            f"(节省 {total_saving}, 节省率 {total_rate:.1f}%)\n\n"
        )

    report_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "docs", "BENCHMARK_REPORT.md"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
