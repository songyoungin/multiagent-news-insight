"""파서 에이전트 구성 모듈."""

from __future__ import annotations

from typing import Any

import httpx
import trafilatura
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from pydantic import ValidationError

from common import NewsDoc
from common.logger import get_logger
from common.prompts import PARSER_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 10.0
MAX_CONCURRENT_REQUESTS = 5

instrument_langfuse()


def parse_articles(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """뉴스 기사 URL에서 본문 텍스트를 추출한다.

    Args:
        documents (list[dict[str, Any]]): `NewsDoc` 스키마와 호환되는 기사 리스트.

    Returns:
        list[dict[str, Any]]: 본문 텍스트가 채워진 기사 리스트.
    """
    if not documents:
        logger.info("No documents provided; returning empty result")
        return []

    logger.info("Parsing articles count=%s", len(documents))

    parsed_documents: list[dict[str, Any]] = []
    for doc_dict in documents:
        try:
            doc = NewsDoc(**doc_dict)
        except ValidationError as exc:
            logger.info("Skip document due to validation error=%s", exc)
            continue

        readable_text = _extract_text_from_url(str(doc.url))
        if readable_text:
            doc.readable_text = readable_text
            parsed_documents.append(doc.model_dump(mode="json"))
        else:
            logger.info("Skip document due to no readable text url=%s", doc.url)

    logger.info("Successfully parsed articles count=%s", len(parsed_documents))
    return parsed_documents


def _extract_text_from_url(url: str) -> str | None:
    """URL에서 HTML을 가져와 본문 텍스트를 추출한다.

    Args:
        url (str): 기사 URL.

    Returns:
        str | None: 추출된 본문 텍스트. 실패 시 None.
    """
    try:
        response = httpx.get(url, timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.info("Failed to fetch URL=%s, error=%s", url, exc)
        return None

    html_content = response.text
    if not html_content:
        logger.info("Empty HTML content for URL=%s", url)
        return None

    extracted_text = trafilatura.extract(html_content, include_comments=False, include_tables=False)
    if not extracted_text or len(extracted_text.strip()) < 100:
        logger.info("No meaningful text extracted from URL=%s", url)
        return None

    return extracted_text.strip()


PARSER_TOOL = FunctionTool(func=parse_articles)
PARSER_MODEL = LiteLlm(model=settings.openai_model, tool_choice="auto")

PARSER_AGENT = LlmAgent(
    name="finance_news_parser_agent",
    model=PARSER_MODEL,
    instruction=PARSER_PROMPT,
    tools=[PARSER_TOOL],
)

logger.info("Parser agent initialized.")
