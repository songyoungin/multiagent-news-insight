"""텔레메트리 및 계측 도우미 모듈."""

from __future__ import annotations

from common.logger import get_logger

logger = get_logger(__name__)


def instrument_langfuse() -> None:
    """Langfuse 계측을 초기화한다.

    환경에 Langfuse SDK가 설치되어 있으면 초기화를 진행하고, 없으면 조용히 건너뛴다.
    """
    try:
        from langfuse import Langfuse  # type: ignore
    except ModuleNotFoundError:
        logger.info("Langfuse SDK not found. Skipping telemetry instrumentation.")
        return

    try:
        Langfuse()  # type: ignore[call-arg]
        logger.info("Langfuse instrumentation completed.")
    except Exception as exc:
        logger.info("Langfuse instrumentation skipped due to error=%s", exc)
