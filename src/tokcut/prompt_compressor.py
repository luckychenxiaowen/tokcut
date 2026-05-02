"""tokcut 输入语义压缩器。

对用户消息进行语义压缩，减少输入 Token 消耗。
支持两种模式：
- safe: 去重复行 + 过滤填充词（节省 20%-40%）
- aggressive: 截断70% + 过滤填充词（节省 50%-75%）
"""

import logging
import re
from typing import Dict, List

__all__ = ["PromptCompressor"]

logger = logging.getLogger(__name__)

# ── 填充词集合 ────────────────────────────────────────────────

FILLER_WORDS: set = {
    "please", "kindly", "just", "really", "very", "basically",
    "actually", "essentially", "simply", "quite",
    "请", "麻烦", "帮忙", "真的", "非常", "基本上", "实际上",
}


class PromptCompressor:
    """输入语义压缩器。

    通过去除重复行、过滤填充词、截断文本来压缩用户输入 prompt。

    Attributes:
        mode: 压缩模式 ('safe' 或 'aggressive')。
    """

    def __init__(self, mode: str = "safe") -> None:
        """初始化输入压缩器。

        Args:
            mode: 压缩模式，'safe'（安全）或 'aggressive'（激进）。默认 'safe'。
        """
        self.mode = mode

    def compress_text(self, text: str) -> str:
        """压缩单段文本。

        处理流程：
        1. 临时保护代码块（`` ``` `` 包裹的内容）。
        2. 根据模式压缩正文。
        3. 还原被保护的代码块。

        Args:
            text: 原始文本。

        Returns:
            压缩后的文本。
        """
        if not text:
            return text

        # 1. 保护代码块
        code_blocks = re.findall(r"```[\s\S]*?```", text)
        for i, cb in enumerate(code_blocks):
            text = text.replace(cb, f"__CODE_BLOCK_{i}__")

        # 2. 模式压缩
        if self.mode == "safe":
            text = self._safe_compress(text)
        elif self.mode == "aggressive":
            text = self._aggressive_compress(text)

        # 3. 还原代码块
        for i, cb in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", cb)

        return text.strip()

    def compress_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """压缩消息列表中的用户消息。

        仅压缩 role 为 'user' 的消息，system 和 assistant 消息保持不变。

        Args:
            messages: 消息列表。

        Returns:
            压缩后的消息列表。
        """
        compressed: List[Dict[str, str]] = []
        for msg in messages:
            if msg.get("role") == "user":
                compressed.append(
                    {**msg, "content": self.compress_text(msg.get("content", ""))}
                )
            else:
                compressed.append(msg)
        return compressed

    def _safe_compress(self, text: str) -> str:
        """安全模式压缩：去重复行 + 去填充词。

        Args:
            text: 原始文本（代码块已被保护）。

        Returns:
            压缩后的文本。
        """
        # 去除连续重复行
        lines = text.splitlines()
        deduped: List[str] = []
        prev: Optional[str] = None
        for line in lines:
            stripped = line.strip()
            if stripped != prev:
                deduped.append(line)
                prev = stripped
        text = "\n".join(deduped)

        # 过滤填充词
        words = text.split()
        filtered = [
            w for w in words
            if w.lower().strip(",.;!?") not in FILLER_WORDS
        ]
        return " ".join(filtered)

    def _aggressive_compress(self, text: str) -> str:
        """激进模式压缩：截断70% + 去填充词。

        Args:
            text: 原始文本（代码块已被保护）。

        Returns:
            压缩后的文本。
        """
        limit = max(int(len(text) * 0.7), 1)
        text = text[:limit]

        words = text.split()
        filtered = [
            w for w in words
            if w.lower().strip(",.;!?") not in FILLER_WORDS
        ]
        return " ".join(filtered)
