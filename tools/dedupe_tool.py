"""문서 중복 제거 툴 모듈."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from google.adk.tools.function_tool import FunctionTool

from common.logger import get_logger

logger = get_logger(__name__)


def dedupe_documents(documents: list[dict[str, Any]], similarity_threshold: float = 0.9) -> list[dict[str, Any]]:
    """문서 리스트에서 URL과 텍스트 유사도를 기반으로 중복 항목을 제거한다.

    Args:
        documents (list[dict[str, Any]]): 중복 제거 대상 문서 리스트.
        similarity_threshold (float): 텍스트 유사도로 판단할 임계값.

    Returns:
        list[dict[str, Any]]: 중복 제거가 완료된 문서 리스트.
    """
    logger.info("Starting dedupe process for size=%s threshold=%s", len(documents), similarity_threshold)
    if not documents:
        logger.info("No documents provided for dedupe")
        return []

    seen_urls: set[str] = set()
    unique_documents: list[dict[str, Any]] = []

    for document in documents:
        if _is_duplicate_by_url(document, seen_urls):
            continue
        if _is_duplicate_by_similarity(document, unique_documents, similarity_threshold):
            continue
        unique_documents.append(document)
        url = document.get("url", "")
        if url:
            seen_urls.add(url)

    logger.info("Finished dedupe process result=%s", len(unique_documents))
    return unique_documents


def create_dedupe_tool() -> FunctionTool:
    """ADK에서 사용 가능한 Dedupe 툴을 생성한다.

    Returns:
        FunctionTool: Dedupe 문서 툴 인스턴스.
    """
    return FunctionTool(func=dedupe_documents)


def _is_duplicate_by_url(document: dict[str, Any], seen_urls: set[str]) -> bool:
    """URL 중복 여부를 판단한다.

    Args:
        document (dict[str, Any]): 검사 대상 문서.
        seen_urls (set[str]): 이미 처리한 URL 집합.

    Returns:
        bool: URL 중복이면 True.
    """
    url = document.get("url")
    if not url:
        return False
    if url in seen_urls:
        logger.info("Skip duplicate document by url=%s", url)
        return True
    return False


def _is_duplicate_by_similarity(
    document: dict[str, Any],
    candidates: list[dict[str, Any]],
    threshold: float,
) -> bool:
    """텍스트 유사도로 문서 중복 여부를 판단한다.

    Args:
        document (dict[str, Any]): 검사 대상 문서.
        candidates (list[dict[str, Any]]): 비교 대상 문서 리스트.
        threshold (float): 텍스트 유사도로 판단할 임계값.

    Returns:
        bool: 유사도가 임계값 이상이면 True.
    """
    target_text = _prepare_comparison_text(document)
    if not target_text:
        return False

    for candidate in candidates:
        candidate_text = _prepare_comparison_text(candidate)
        if not candidate_text:
            continue
        similarity = SequenceMatcher(None, target_text, candidate_text).ratio()
        if similarity >= threshold:
            logger.info("Skip duplicate document by similarity=%s", similarity)
            return True
    return False


def _prepare_comparison_text(document: dict[str, Any]) -> str:
    """중복 판단을 위한 비교 텍스트를 생성한다.

    Args:
        document (dict[str, Any]): 비교용 텍스트를 추출할 문서.

    Returns:
        str: 정규화된 비교 텍스트. 적절한 텍스트가 없으면 빈 문자열.
    """
    title = document.get("title", "")
    readable_text = document.get("readable_text", "")
    combined = " ".join(part for part in (title, readable_text) if part)
    if not combined:
        return ""
    normalized = " ".join(combined.lower().split())
    return normalized
