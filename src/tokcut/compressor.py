"""tokcut 输出风格压缩器。

核心模块之一，通过两层机制降低 LLM 输出 Token 消耗：
1. 注入式压缩：在 system prompt 末尾追加 Caveman 风格指令，引导模型输出简洁内容。
2. 后处理兜底：对未完全遵循指令的响应执行规则化缩减。

技术内容（代码块、URL、数字等）通过 ContentProtector 保护后不会被压缩。
"""

import logging
import re
from typing import Any, Dict, List

from .protector import ContentProtector

__all__ = ["OutputCompressor"]

logger = logging.getLogger(__name__)

# ── 压缩指令模板 ──────────────────────────────────────────────

COMPRESSION_PROMPTS: Dict[str, str] = {
    "lite": (
        "You are in token-saving mode. Omit all polite phrases, greetings, "
        "and filler words. Keep responses concise but grammatically complete. "
        "Protect all code, URLs, numbers exactly."
    ),
    "full": (
        "CRITICAL: Extremely concise mode. Drop articles, pronouns, and all "
        "unnecessary words. Respond with keywords and essential information only. "
        "Do not use any markdown formatting unless absolutely required. "
        "Protect code, URLs, numbers verbatim."
    ),
    "ultra": (
        "ULTRA BRIEF MODE. Only key info. No sentences. Single words or fragments. "
        "Output: answer only. No intro, no outro, no explanation unless user asks. "
        "Protect technical strings exactly."
    ),
}


class OutputCompressor:
    """输出风格压缩器，通过 system prompt 注入和后处理来降低输出 Token。

    Attributes:
        level: 压缩等级 ('lite', 'full', 'ultra')。
        protector: ContentProtector 实例，用于保护技术内容不被压缩。
    """

    def __init__(self, level: str = "full") -> None:
        """初始化压缩器。

        Args:
            level: 压缩等级，可选 'lite'、'full'、'ultra'。默认 'full'。
        """
        self.level = level
        self.protector = ContentProtector()

    def enhance_system_prompt(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """在消息列表的 system prompt 中注入压缩指令。

        如果消息列表中已有 system 角色消息，则将压缩指令追加到其 content 末尾；
        否则新建一条 system 消息。

        Args:
            messages: 原始消息列表，每条包含 'role' 和 'content'。

        Returns:
            注入压缩指令后的新消息列表。
        """
        prompt_text = COMPRESSION_PROMPTS.get(
            self.level, COMPRESSION_PROMPTS["full"]
        )
        new_messages: List[Dict[str, Any]] = []
        system_found = False

        for msg in messages:
            if msg["role"] == "system":
                new_content = (
                    msg["content"] + "\n\n" + prompt_text
                    if msg["content"]
                    else prompt_text
                )
                new_messages.append({"role": "system", "content": new_content})
                system_found = True
            else:
                new_messages.append(msg)

        if not system_found:
            new_messages.insert(0, {"role": "system", "content": prompt_text})

        return new_messages

    def post_process(self, text: str) -> str:
        """对 LLM 响应文本执行后处理规则压缩。

        步骤：
        1. 使用 ContentProtector 保护技术内容。
        2. 删除常见的引导语和客套话（中英文）。
        3. 压缩多余空格。
        4. 还原被保护的技术内容。

        Args:
            text: LLM 原始响应文本。

        Returns:
            压缩后的文本。
        """
        if not text:
            return text

        try:
            protected = self.protector.protect(text)

            # 删除常见引导语（中英文）
            polite_patterns = (
                r"^(Sure!?|I'd be happy to|Certainly!?|Here you go|"
                r"Of course|Absolutely|好的[，,]?|当然[，,]?|"
                r"没问题[，,]?|让我来|请注意|您好|很高兴|"
                r"下面是|以下是|以下为)[,:，。!]?\s*"
            )
            protected = re.sub(
                polite_patterns, "", protected, flags=re.IGNORECASE
            )

            # 压缩多余空格
            protected = re.sub(r"\s+", " ", protected).strip()

            result = self.protector.restore(protected)
            return result
        except Exception as e:
            logger.warning(f"Post-processing failed: {e}, returning original text")
            return text
