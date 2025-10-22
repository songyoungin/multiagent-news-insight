"""크롤러 에이전트 구성 모듈."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from pydantic import ValidationError

from common import NewsDoc
from common.logger import get_logger
from common.prompts import CRAWLER_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse

logger = get_logger(__name__)

NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

instrument_langfuse()


def crawl_news(
    query: str,
    lookback_hours: int = 24,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    """NewsAPI에서 금융 뉴스를 수집한다.

    Args:
        query (str): 검색어 문자열.
        lookback_hours (int): 조회 기간(시간 단위).
        page_size (int): 페이지당 기사 수.

    Returns:
        list[dict[str, Any]]: `NewsDoc` 스키마와 호환되는 기사 리스트.
    """

    api_key = settings.newsapi_api_key
    if not query:
        logger.info("Query is empty; returning empty result")
        return []
    if not api_key:
        logger.info("NewsAPI key missing; returning empty result")
        return []

    logger.info("Crawling news for query=%s, lookback_hours=%s, page_size=%s", query, lookback_hours, page_size)

    normalized_page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    published_after = (datetime.now(UTC) - timedelta(hours=max(1, lookback_hours))).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "from": published_after,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": normalized_page_size,
    }
    headers = {"X-Api-Key": api_key}

    try:
        response = httpx.get(NEWS_API_ENDPOINT, params=params, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.info("NewsAPI request failed: %s", exc)
        return []

    payload = response.json()
    articles = payload.get("articles") or []

    if not articles:
        logger.info("No articles found in NewsAPI response")
        return []

    documents: list[dict[str, Any]] = []
    for article in articles:
        document = _article_to_document(article)
        if document is not None:
            documents.append(document)

    logger.info("Collected articles count=%s", len(documents))
    return documents


def _article_to_document(article: dict[str, Any]) -> dict[str, Any] | None:
    """NewsAPI 기사 응답을 `NewsDoc` 구조로 변환한다.

    Args:
        article (dict[str, Any]): NewsAPI 기사 응답.

    Returns:
        dict[str, Any] | None: 변환된 기사. 필수 필드가 없으면 None.
    """
    logger.info("Converting article to document=%s", article)
    url = article.get("url")
    title = article.get("title")
    publisher = _extract_publisher(article)
    published_at_raw = article.get("publishedAt")

    if not url or not title or not publisher or not published_at_raw:
        logger.info("Skip article due to missing fields url=%s", url)
        return None

    published_at = _parse_published_at(published_at_raw)
    if published_at is None:
        logger.info("Skip article due to invalid published_at url=%s", url)
        return None

    try:
        document = NewsDoc(
            url=url,
            title=title,
            publisher=publisher,
            published_at=published_at,
            readable_text=None,
        )
    except ValidationError as exc:
        logger.info("Skip article due to validation error=%s", exc)
        return None

    return document.model_dump()


def _parse_published_at(raw_value: str) -> datetime | None:
    """문자열 형태의 발행 시각을 파싱한다.

    Args:
        raw_value (str): ISO8601 포맷 문자열.

    Returns:
        datetime | None: 파싱된 시각. 실패 시 None.
    """
    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _extract_publisher(article: dict[str, Any]) -> str | None:
    """기사 응답에서 발행 매체 정보를 추출한다.

    Args:
        article (dict[str, Any]): NewsAPI 기사 응답.

    Returns:
        str | None: 발행 매체 이름.
    """
    source = article.get("source") or {}
    name = source.get("name")
    if name:
        return str(name)

    url = article.get("url")
    if not url:
        return None

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname


CRAWLER_TOOL = FunctionTool(func=crawl_news)
CRAWLER_MODEL = LiteLlm(model=settings.openai_model, tool_choice="auto")

CRAWLER_AGENT = LlmAgent(
    name="finance_news_crawler_agent",
    model=CRAWLER_MODEL,
    instruction=CRAWLER_PROMPT,
    tools=[CRAWLER_TOOL],
)

logger.info("Crawler agent initialized.")
