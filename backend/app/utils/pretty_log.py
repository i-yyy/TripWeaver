"""终端友好的结构化日志输出工具。"""

from __future__ import annotations

import logging
from typing import Optional

_WIDTH = 60


def _emit(message: str, logger: Optional[logging.Logger] = None, level: str = "info") -> None:
    if logger is None:
        print(message)
        return
    log_fn = getattr(logger, level, logger.info)
    log_fn(message)


def separator(logger: Optional[logging.Logger] = None) -> None:
    _emit("=" * _WIDTH, logger=logger)


def spacer(logger: Optional[logging.Logger] = None) -> None:
    _emit("", logger=logger)


def section(title: str, icon: str = "", logger: Optional[logging.Logger] = None) -> None:
    spacer(logger=logger)
    separator(logger=logger)
    line = f"{icon} {title}".strip()
    _emit(line, logger=logger)
    separator(logger=logger)
    spacer(logger=logger)


def kv(key: str, value: object, logger: Optional[logging.Logger] = None, indent: int = 0) -> None:
    space = " " * indent
    _emit(f"{space}{key}: {value}", logger=logger)


def info(message: str, logger: Optional[logging.Logger] = None) -> None:
    _emit(f"🔄 {message}", logger=logger)


def ok(message: str, logger: Optional[logging.Logger] = None) -> None:
    _emit(f"✅ {message}", logger=logger)


def warn(message: str, logger: Optional[logging.Logger] = None) -> None:
    _emit(f"⚠️  {message}", logger=logger, level="warning")


def error(message: str, logger: Optional[logging.Logger] = None) -> None:
    _emit(f"❌ {message}", logger=logger, level="error")
