"""감정 분석 에이전트 구성 모듈."""

from __future__ import annotations

import re
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from pydantic import ValidationError

from common import NewsDoc
from common.logger import get_logger
from common.prompts import SENTIMENT_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse

logger = get_logger(__name__)

instrument_langfuse()

# 감정 분석용 키워드 사전
POSITIVE_KEYWORDS = {
    "surge",
    "soar",
    "rally",
    "gain",
    "profit",
    "growth",
    "success",
    "breakthrough",
    "bullish",
    "upgrade",
    "optimistic",
    "beat",
    "exceed",
    "strong",
    "rise",
    "increase",
    "up",
    "high",
    "record",
    "boost",
    "win",
    "positive",
    "innovative",
    "outperform",
}

NEGATIVE_KEYWORDS = {
    "plunge",
    "crash",
    "fall",
    "loss",
    "decline",
    "bearish",
    "downgrade",
    "pessimistic",
    "miss",
    "weak",
    "drop",
    "decrease",
    "down",
    "low",
    "fail",
    "negative",
    "concern",
    "risk",
    "warning",
    "cut",
    "layoff",
    "bankruptcy",
    "recession",
    "crisis",
    "underperform",
}

FINANCIAL_KEYWORDS = {
    "stock",
    "market",
    "trading",
    "investor",
    "earnings",
    "revenue",
    "profit",
    "quarter",
    "share",
    "price",
    "financial",
    "economic",
    "fed",
    "rate",
    "inflation",
    "gdp",
    "nasdaq",
    "dow",
    "s&p",
    "wall street",
    "equity",
    "bond",
    "commodity",
    "forex",
    "analyst",
    "forecast",
    "outlook",
    "guidance",
    "dividend",
    "acquisition",
    "merger",
}


def analyze_sentiment(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """뉴스 기사의 감정과 금융 관련도를 분석한다.

    Args:
        documents (list[dict[str, Any]]): `NewsDoc` 스키마�� 호��되는 기사 리스트.

    Returns:
        list[dict[str, Any]]: 각 기사의 감정 및 관련도 정보가 포함된 결과 리스트.
            형식: [{"document": {...}, "sentiment": float, "relevance": float}, ...]
    """
    if not documents:
        logger.info("No documents provided; returning empty result")
        return []

    logger.info("Analyzing sentiment for documents count=%s", len(documents))

    results: list[dict[str, Any]] = []
    for doc_dict in documents:
        try:
            doc = NewsDoc(**doc_dict)
        except ValidationError as exc:
            logger.info("Skip document due to validation error=%s", exc)
            continue

        if not doc.readable_text:
            logger.info("Skip document due to missing text url=%s", doc.url)
            continue

        text = (doc.title + " " + doc.readable_text).lower()

        sentiment_score = _calculate_sentiment(text)
        relevance_score = _calculate_relevance(text)

        results.append(
            {
                "document": doc.model_dump(mode="json"),
                "sentiment": sentiment_score,
                "relevance": relevance_score,
            }
        )

    logger.info("Sentiment analysis completed for %s documents", len(results))
    return results


def _calculate_sentiment(text: str) -> float:
    """텍스트의 감정 점수를 계산한다.

    Args:
        text (str): 분석할 텍스트 (소문자 변환된 상태).

    Returns:
        float: -1.0 (부정) ~ 0.0 (중립) ~ 1.0 (긍정) 범위의 감정 점수.
    """
    positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text)
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)

    total_count = positive_count + negative_count
    if total_count == 0:
        return 0.0

    # 긍정/부정 비율로 점수 계산
    sentiment = (positive_count - negative_count) / total_count
    # -1.0 ~ 1.0 범위로 정규화
    return max(-1.0, min(1.0, sentiment))


def _calculate_relevance(text: str) -> float:
    """텍스트의 금융 관련도를 계산한다.

    Args:
        text (str): 분석할 텍스트 (소문자 변환된 상태).

    Returns:
        float: 0.0 ~ 1.0 범위의 관련도 점수.
    """
    financial_count = sum(1 for keyword in FINANCIAL_KEYWORDS if keyword in text)

    # 단어 수 기준으로 정규화
    word_count = len(re.findall(r"\b\w+\b", text))
    if word_count == 0:
        return 0.0

    # 금융 키워드 밀도 계산 (1000단어당)
    density = (financial_count / word_count) * 1000

    # 0.0 ~ 1.0 범위로 정규화 (밀도 10 이상이면 1.0)
    relevance = min(1.0, density / 10.0)
    return round(relevance, 2)


SENTIMENT_TOOL = FunctionTool(func=analyze_sentiment)
SENTIMENT_MODEL = LiteLlm(model=settings.openai_model, tool_choice="auto")

SENTIMENT_AGENT = LlmAgent(
    name="finance_news_sentiment_agent",
    model=SENTIMENT_MODEL,
    instruction=SENTIMENT_PROMPT,
    tools=[SENTIMENT_TOOL],
)

logger.info("Sentiment agent initialized.")
