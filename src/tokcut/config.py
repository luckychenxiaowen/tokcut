"""tokcut 配置管理模块。

支持 YAML 配置文件加载，并提供合理的默认值。
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

__all__ = ["DEFAULT_CONFIG", "load_config"]

logger = logging.getLogger(__name__)

# ── 默认配置 ──────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "compressor": {
        "level": "full",
        "enabled": True,
        "protect_patterns": [
            r"```[\s\S]*?```",
            r"`[^`]+`",
            r"https?://\S+",
            r"\b\d+(?:\.\d+)?\b",
            r"[\w\-_]+(?:\.[\w\-_]+)+",
        ],
    },
    "prompt_compressor": {
        "enabled": False,
        "mode": "safe",
    },
    "cache": {
        "enabled": True,
        "backend": "memory",
        "sqlite_path": "./cache.db",
        "similarity_threshold": 0.95,
        "ttl_minutes": 60,
    },
    "upstream": {},
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置。

    优先级：用户配置文件 > 环境变量覆盖 > 默认值。

    Args:
        config_path: YAML 配置文件路径。为 None 时使用默认配置。

    Returns:
        合并后的配置字典。
    """
    config = dict(DEFAULT_CONFIG)  # shallow copy

    if config_path and Path(config_path).exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
            if isinstance(user_config, dict):
                config = _deep_merge(config, user_config)
            logger.info(f"Loaded config from: {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    else:
        logger.info("Using default configuration")

    return config


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典。

    Args:
        base: 基础字典。
        override: 覆盖字典。

    Returns:
        合并后的新字典。
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
