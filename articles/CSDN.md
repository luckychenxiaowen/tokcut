# 写了个透明代理，把 DeepSeek / GLM / Kimi 的 Token 消耗砍了 40%+

> 从 Caveman 的 prompt 骚操作说起，到掏出一个 33 个文件、三层压缩引擎的开源代理 —— 全程用 DeepSeek + CodeBuddy 干的。

---

## 一、起因：一个 GitHub 小项目让我睡不着觉

前几天刷 GitHub Trending，撞见一个叫 [Caveman](https://github.com/JuliusBrussee/caveman) 的项目。

这玩意做的事特简单：往 system prompt 里塞一段「给我说人话，别整那些虚的」，强制 Claude 删掉所有礼貌用语、过渡词、冗余修饰。

结果直接给我看傻了：**在 Claude Code 里实测平均省了 65% 的输出 Token**。

65%。我盯着这个数字看了好几秒。你要是一个月 LLM API 开销一万块，光改一下 system prompt 就能省六千五。什么概念？差不多白捡一个中配云服务器。

但 Caveman 只管输出，输入完全没碰，也没有缓存。而且它是冲着 Claude Code 这个具体场景做的，换个模型就不一定好使了。

我当时脑子里就一个念头：能不能包个更大的——输入压缩、输出压缩、语义缓存全塞进一层透明代理，让只要兼容 OpenAI 接口的模型都能用？

---

## 二、方案设计：从 10 种 Token 压缩手段里挑出性价比最高的 3 种

我先花了一个多小时把全网能搜到的 Token 节省方案捋了一遍，列了个表：

| # | 方法 | 层级 | 预期节省 | 实施难度 | 我选吗 |
|---|------|------|----------|----------|--------|
| T1 | 输出风格压缩（Caveman） | 应用层 | 40%-75% | 低 | ✅ |
| T2 | Prompt 语义压缩 | 应用层 | 40%-75% | 中 | ✅ |
| T3 | 结构化意图提取 | 应用层 | 30%-50% | 中 | ❌ |
| T4 | 语义缓存 | 逻辑层 | 50%-90% | 中 | ✅ |
| T5 | 本地路由 | 逻辑层 | 45%-79% | 高 | ❌ |
| T6 | 本地起草+云端审阅 | 逻辑层 | 51% | 高 | ❌ |
| T7 | 最小化 Diff 编辑 | 逻辑层 | 60%-80% | 高 | ❌ |
| T8 | 批量请求+厂商缓存 | 逻辑层 | 50%-90% | 中 | ❌ |
| T9 | CoT 压缩（TokenSkip） | 模型层 | 40% | 高 | ❌ |
| T10 | KV Cache 压缩 | 模型层 | 30%-60% | 高 | ❌ |

说白了就一个原则：**哪个最简单、最通用、不绑定某个具体模型，就用哪个**。

于是 T1 + T2 + T4，三板斧拍板。

---

## 三、架构设计：一个透明代理，零侵入

核心思路是把一切复杂性封装在代理层里，对上对下都伪装成标准 OpenAI API：

```
你的应用 (OpenAI SDK)
       │
       ▼
  ┌─────────────────────────┐
  │      tokcut 代理          │
  │                          │
  │  ① 语义缓存检查          │ ← sentence-transformers
  │     ├─ 命中 → 直接返回   │    相似度 > 0.95 → 命中
  │     └─ 未命中 ↓         │
  │  ② 输入语义压缩          │ ← safe / aggressive
  │  ③ 输出风格压缩增强      │ ← lite / full / ultra
  │  ④ 转发到上游 LLM       │ ← httpx 异步
  │  ⑤ 响应后处理            │ ← 正则 + ContentProtector
  │  ⑥ 缓存 + 返回 + 统计   │ ← memory / sqlite
  └─────────────────────────┘
       │
       ▼
  任意 OpenAI 兼容 API
  (DeepSeek / GLM / Kimi / ...)
```

客户端代码一行都不用改，只把 `base_url` 换成 `http://localhost:8800/v1` 就完事。

---

## 四、核心模块拆解（带关键代码）

### 4.1 ContentProtector —— 别把代码也给「优化」了

说实话，这个模块是整个系统里最不起眼但最要命的。你想想，你对着 LLM 输出一通正则，把「你好」「请问」全删了，但一不小心把代码块、URL、版本号也顺手剁了——那省下来的 token 有个屁用。

所以我在压缩前先用占位符把技术内容包起来：

```python
class ContentProtector:
    def protect(self, text: str) -> str:
        self.placeholders = {}
        for i, pat in enumerate(self.patterns):
            def repl(m, idx=i):
                key = f"__PROTECTED_{idx}_{len(self.placeholders)}__"
                self.placeholders[key] = m.group(0)
                return key
            text = re.sub(pat, repl, text)
        return text

    def restore(self, text: str) -> str:
        for key, value in self.placeholders.items():
            text = text.replace(key, value)
        return text
```

默认保护模式涵盖：代码块（\`\`\`）、行内代码（\`）、URL、数字（含小数）、文件路径。

### 4.2 OutputCompressor —— 注入式 + 后处理双保险

这东西分两步走。

**第一步，注入式**：在 system prompt 末尾追加压缩指令。我设计了三个档位：

```python
COMPRESSION_PROMPTS = {
    "lite": "省略礼貌用语，保持语法完整",
    "full": "删除冠词和代词，只用关键词。不用任何 markdown。",
    "ultra": "只输出答案。不要完整句子。不要解释。"
}
```

`full` 档最实用，实测输出省 50%-65%，可读性还能接受。`ultra` 太激进，适合机器对机器的场景。

**第二步，后处理兜底**：对于没完全听指令的模型，用正则把中英文引导语全干掉：

```python
polite_patterns = (
    r"^(Sure|好的|当然|没问题|让我来|请注意|您好|下面是)..."
)
protected = re.sub(polite_patterns, "", protected, flags=re.IGNORECASE)
```

### 4.3 SemanticCache —— 用向量相似度做缓存

这可能是三个模块里 ROI 最高的。思路很粗暴：用 `sentence-transformers` 把用户请求转成 embedding，然后和已有缓存做余弦相似度计算，超过阈值直接返回历史响应。

```python
class SemanticCache:
    def get(self, messages: list) -> Optional[Dict]:
        query_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        query_emb = self.model.encode(query_text)
        
        for key, entry in self.memory_cache.items():
            if time.time() - entry["timestamp"] > self.ttl:
                continue
            sim = (query_emb @ entry["embedding"]) / (
                query_emb.dot(query_emb)**0.5 * entry["embedding"].dot(entry["embedding"])**0.5
            )
            if sim >= self.threshold:
                return entry["response"]
        return None
```

用了延迟加载模型的设计——只有第一次查询时才初始化 `SentenceTransformer`，避免启动时就吃 80MB 内存。

### 4.4 server.py —— 把一切串起来

FastAPI 路由层，核心流程 51 行逻辑：

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # 1. 解析请求 & 上游地址
    # 2. 缓存检查 → 命中直接返回
    # 3. 输入压缩（可选）
    # 4. 注入压缩指令到 system prompt
    # 5. httpx 异步转发到上游 LLM
    # 6. 响应后处理压缩
    # 7. 缓存响应 + 统计信息
```

还做了三个工程细节：
- **动态控制**：通过 `X-Tokcut-Compress` / `X-Tokcut-Level` 等 Header 按请求覆盖配置，不用重启
- **自动匹配上游**：如果没传 `X-Provider-URL`，系统会根据 model 字段自动匹配已知厂商的 API 地址
- **结构化统计**：每个响应里塞一个 `tokcut` 字段，记录压缩前后的 Token 数

---

## 五、测试效果：5 个模型 × 5 类任务，平均省 41%

我在 DeepSeek-V3、GLM-4、MiniMax-M2.5、混元、Kimi 上各跑了 5 类任务（代码修复、文本总结、知识问答、翻译、客服对话），共 25 个用例：

| 模型 | 输出节省 | 总节省率 |
|------|---------|---------|
| DeepSeek-V3 | 58% | **42%** |
| GLM-4 | 55% | **41%** |
| MiniMax-M2.5 | 62% | **44%** |
| 混元 | 50% | **40%** |
| Kimi | 60% | **38%** |

用了 `full` 压缩档位 + 内存缓存，输入压缩关着（想保守一点）。

有意思的发现：国产模型对 Caveman 风格指令的响应比想象的更好，尤其是 MiniMax 和 DeepSeek，压缩后输出仍然很准确。反而是某些宣称「很懂中文」的模型，压缩后偶尔丢关键信息——这正好说明 ContentProtector 的价值。

---

## 六、我是怎么开发的

不瞒你说，这 33 个文件我基本没手写几行。全程 **DeepSeek + CodeBuddy** 搭的：

1. 先用 DeepSeek 把设计文档吐出来——模块怎么拆、接口怎么定、数据怎么流
2. 然后喂给 CodeBuddy，让它按文档生成全部工程文件——源码、配置、Docker、CI/CD、文档，一口气出来
3. 跑测试、改 bug、调参数，来回来去几轮
4. 最后对着 Litellm、AutoGPT 这些明星项目的样子，补上了 CONTRIBUTING、SECURITY、CHANGELOG、Issue 模板，搞了中英文双语文档

前前后后一个下午加一个晚上。说实话，放以前，光搭项目架子我就得花两天。但不是说 AI 替我写了就完事了——设计文档里的那些决策，什么模块拆几个、接口怎么定，还是得自己琢磨。AI 擅长的是「知道要写什么，帮你写出来」这一步。

---

## 七、仓库地址

**GitHub**: [github.com/luckychenxiaowen/tokcut](https://github.com/luckychenxiaowen/tokcut)

```bash
git clone https://github.com/luckychenxiaowen/tokcut.git
cd tokcut
pip install -e .
python -m tokcut.server
# → http://localhost:8800
```

一个 curl 试一下：

```bash
curl -X POST http://localhost:8800/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "X-Provider-URL: https://api.deepseek.com/v1/chat/completions" \
  -H "X-Tokcut-Level: full" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"解释 React useEffect"}]}'
```

---

## 八、后续想做的

- **流式响应支持**：现在只支持非流式，SSE 模式要补上
- **更多缓存后端**：Redis 支持，适合分布式部署
- **可观测性面板**：做一个简单的 Web 界面展示节省统计
- **本地路由判断**：简单问题直接走本地小模型，不再调云端 API

欢迎提 Issue 或 PR，更欢迎直接拿去用然后给我反馈。
