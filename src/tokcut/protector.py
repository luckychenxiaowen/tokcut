"""tokcut 内容保护器。

在压缩前后保护技术内容不被损坏。使用占位符机制：
- 压缩前：将代码块、URL、数字等替换为占位符。
- 压缩后：将占位符还原为原始内容。
"""

import re
from typing import Dict, List, Optional

__all__ = ["ContentProtector"]

# ── 默认保护模式 ──────────────────────────────────────────────

DEFAULT_PATTERNS: List[str] = [
    r"```[\s\S]*?```",       # 代码块
    r"`[^`]+`",              # 行内代码
    r"https?://\S+",         # URL
    r"\b\d+(?:\.\d+)?\b",    # 版本号/数字
    r"[\w\-_]+(?:\.[\w\-_]+)+",  # 文件路径
]


class ContentProtector:
    """内容保护器 —— 用占位符包裹受保护内容，压缩后再还原。

    Attributes:
        patterns: 正则模式列表，匹配需要保护的内容。
        placeholders: 占位符 → 原始内容的映射字典。
    """

    def __init__(self, patterns: Optional[List[str]] = None) -> None:
        """初始化保护器。

        Args:
            patterns: 自定义正则模式列表。为 None 时使用默认模式。
        """
        self.patterns: List[str] = patterns or DEFAULT_PATTERNS
        self.placeholders: Dict[str, str] = {}

    def protect(self, text: str) -> str:
        """用占位符替换所有匹配的受保护内容。

        Args:
            text: 原始文本。

        Returns:
            占位符替换后的文本。
        """
        self.placeholders = {}

        for i, pat in enumerate(self.patterns):
            def repl(match: re.Match, idx: int = i) -> str:
                key = f"__PROTECTED_{idx}_{len(self.placeholders)}__"
                self.placeholders[key] = match.group(0)
                return key

            text = re.sub(pat, repl, text)

        return text

    def restore(self, text: str) -> str:
        """将占位符还原为原始内容。

        Args:
            text: 包含占位符的文本。

        Returns:
            还原后的文本。
        """
        for key, value in self.placeholders.items():
            text = text.replace(key, value)
        return text
