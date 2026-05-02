"""
DeepSeek 真实 API 对比测试：压缩版 system prompt vs 普通 prompt
直接调 DeepSeek API，不依赖本地代理服务，数据更纯粹。
"""
import time, json, os
import httpx

API_KEY = "sk-a6884d3c94a544c78f9fe6812fc0636b"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# 压缩指令（和 compressor.py 完全一致）
COMPRESSION_INSTRUCTIONS = {
    "full": (
        "CRITICAL: Extremely concise mode. Drop articles, pronouns, and all unnecessary words. "
        "Respond with keywords and essential information only. "
        "Do not use any markdown formatting unless absolutely required. "
        "Protect code, URLs, numbers verbatim."
    ),
    "ultra": (
        "ULTRA BRIEF MODE. Only key info. No sentences. Single words or fragments. "
        "Output: answer only. No intro, no outro, no explanation unless user asks. "
        "Protect technical strings exactly."
    ),
}

# 5 类任务
TASKS = [
    ("代码修复", "我的 React 组件每次父组件更新时都重新渲染，尽管我用了 React.memo。请说明可能的原因有哪些，并给我修复代码。"),
    ("文本总结", "请总结：今天上午我们召开了产品规划会议，讨论了A、B、C三个功能的优先级，最终决定先做A功能，因为它对用户增长最有利。下午又和技术团队确认了排期，预计两周内完成。"),
    ("知识问答", "什么是大语言模型中的 RLHF？请解释其核心原理。"),
    ("翻译任务", "把下面英文翻译成中文：The development of AI has transformed industries, but also raises ethical concerns about privacy and employment."),
    ("对话任务", "用户说：我的订单三天了还没发货。你是客服，请给出一个专业回复。"),
]


def call_deepseek(client, prompt, system_prompt=None):
    """调用 DeepSeek API，可选增强 system prompt"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"model": MODEL, "messages": messages}

    t0 = time.time()
    resp = client.post(DEEPSEEK_URL, json=body, headers=headers, timeout=120)
    elapsed = time.time() - t0
    data = resp.json()
    usage = data.get("usage", {})
    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""

    return {
        "content": content,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "elapsed": elapsed,
    }


def main():
    print("=" * 60)
    print(" DeepSeek REAL API Benchmark")
    print(" Compression-enhanced system prompt vs No compression")
    print("=" * 60)

    results = {"baseline": [], "full": [], "ultra": []}

    with httpx.Client(http2=False, timeout=120) as client:
        for i, (task, prompt) in enumerate(TASKS):
            print(f"\n[{i+1}/5] {task}")
            print(f"  Prompt: {prompt[:70]}...")

            # 1) 基线：不压缩
            base = call_deepseek(client, prompt)
            results["baseline"].append(base)
            print(f"  No compression: in={base['prompt_tokens']} out={base['completion_tokens']} "
                  f"total={base['total_tokens']} ({base['elapsed']:.1f}s)")
            print(f"  Content: {base['content'][:100]}...")
            time.sleep(2)

            # 2) full 级别压缩
            full = call_deepseek(client, prompt, COMPRESSION_INSTRUCTIONS["full"])
            results["full"].append(full)
            saved = base["total_tokens"] - full["total_tokens"]
            rate = (saved / base["total_tokens"] * 100) if base["total_tokens"] else 0
            print(f"  Full compress: in={full['prompt_tokens']} out={full['completion_tokens']} "
                  f"total={full['total_tokens']} ({full['elapsed']:.1f}s)")
            print(f"  Content: {full['content'][:100]}...")
            print(f"  >> Saved: {saved} tokens ({rate:.1f}%)")
            time.sleep(2)

            # 3) ultra 级别压缩
            ultra = call_deepseek(client, prompt, COMPRESSION_INSTRUCTIONS["ultra"])
            results["ultra"].append(ultra)
            saved = base["total_tokens"] - ultra["total_tokens"]
            rate = (saved / base["total_tokens"] * 100) if base["total_tokens"] else 0
            print(f"  Ultra compress: in={ultra['prompt_tokens']} out={ultra['completion_tokens']} "
                  f"total={ultra['total_tokens']} ({ultra['elapsed']:.1f}s)")
            print(f"  Content: {ultra['content'][:100]}...")
            print(f"  >> Saved: {saved} tokens ({rate:.1f}%)")
            time.sleep(2)

    # 汇总
    print("\n" + "=" * 60)
    print(" FINAL RESULTS")
    print("=" * 60)

    for level in ["full", "ultra"]:
        print(f"\n  --- {level.upper()} Compression ---")
        total_base = 0
        total_comp = 0
        for i, task_name in enumerate([t[0] for t in TASKS]):
            b = results["baseline"][i]["total_tokens"]
            c = results[level][i]["total_tokens"]
            total_base += b
            total_comp += c
            s = b - c
            r = (s / b * 100) if b else 0
            bar = "#" * max(int(r/3), 1)
            print(f"  {task_name:8s} | {b:5d} -> {c:5d} | save {s:4d} ({r:5.1f}%) {bar}")

        overall_save = total_base - total_comp
        overall_rate = (overall_save / total_base * 100) if total_base else 0
        print(f"  {'TOTAL':8s} | {total_base:5d} -> {total_comp:5d} | save {overall_save:4d} ({overall_rate:5.1f}%)")

        # Separate input/output stats
        in_base = sum(results["baseline"][i]["prompt_tokens"] for i in range(len(TASKS)))
        in_comp = sum(results[level][i]["prompt_tokens"] for i in range(len(TASKS)))
        out_base = sum(results["baseline"][i]["completion_tokens"] for i in range(len(TASKS)))
        out_comp = sum(results[level][i]["completion_tokens"] for i in range(len(TASKS)))
        out_rate = ((out_base - out_comp) / out_base * 100) if out_base else 0
        print(f"  Output token save: {out_base} -> {out_comp} ({out_rate:.1f}%)")

    # 保存结果
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "real_bench_results.json")
    # 转成可序列化格式
    serializable = {
        "tasks": [t[0] for t in TASKS],
        "prompts": [t[1] for t in TASKS],
        "baseline": results["baseline"],
        "full": results["full"],
        "ultra": results["ultra"],
        "summary_full": {
            "total_base": sum(r["total_tokens"] for r in results["baseline"]),
            "total_full": sum(r["total_tokens"] for r in results["full"]),
            "out_base": sum(r["completion_tokens"] for r in results["baseline"]),
            "out_full": sum(r["completion_tokens"] for r in results["full"]),
        },
        "summary_ultra": {
            "total_base": sum(r["total_tokens"] for r in results["baseline"]),
            "total_ultra": sum(r["total_tokens"] for r in results["ultra"]),
            "out_base": sum(r["completion_tokens"] for r in results["baseline"]),
            "out_ultra": sum(r["completion_tokens"] for r in results["ultra"]),
        },
    }
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {result_path}")


if __name__ == "__main__":
    main()
