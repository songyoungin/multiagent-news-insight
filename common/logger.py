"""공통 로깅 유틸리티 모듈."""

from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO)


def get_logger(name: str | None = None) -> logging.Logger:
    """로거 인스턴스를 반환한다.

    Args:
        name (str | None): 로거 이름. 지정하지 않으면 기본 이름을 사용한다.

    Returns:
        logging.Logger: 요청된 이름의 로거 인스턴스.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger("multiagent-news-insight")
