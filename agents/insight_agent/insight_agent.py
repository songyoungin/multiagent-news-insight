"""인사이트 생성 에이전트 구성 모듈."""

from __future__ import annotations

from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from litellm import completion

from common import Insight
from common.logger import get_logger
from common.prompts import INSIGHT_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse

logger = get_logger(__name__)

instrument_langfuse()

MIN_RELEVANCE_THRESHOLD = 0.3
HIGH_SENTIMENT_THRESHOLD = 0.3


def generate_insights(sentiment_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """감정 분석 결과를 바탕으로 실행 가능한 인사이트를 생성한다.

    Args:
        sentiment_results (list[dict[str, Any]]): 감정 분석 결과 리스트.
            각 항목은 {"document": {...}, "sentiment": float, "relevance": float} 형태.

    Returns:
        list[dict[str, Any]]: 인사이트 리스트. Insight 스키마와 호환.
    """
    if not sentiment_results:
        logger.info("No sentiment results provided; returning empty result")
        return []

    logger.info("Generating insights from sentiment results count=%s", len(sentiment_results))

    # 관련도가 높은 기사만 필터링
    relevant_results = [item for item in sentiment_results if item.get("relevance", 0.0) >= MIN_RELEVANCE_THRESHOLD]

    if not relevant_results:
        logger.info("No relevant articles found; returning empty result")
        return []

    # 감정별로 그룹화
    positive_articles = [item for item in relevant_results if item.get("sentiment", 0.0) >= HIGH_SENTIMENT_THRESHOLD]
    negative_articles = [item for item in relevant_results if item.get("sentiment", 0.0) <= -HIGH_SENTIMENT_THRESHOLD]

    insights: list[dict[str, Any]] = []

    # 긍정 인사이트 생성
    if positive_articles:
        positive_insight = _generate_sentiment_insight(
            positive_articles,
            sentiment_type="positive",
        )
        if positive_insight:
            insights.append(positive_insight)

    # 부정 인사이트 생성
    if negative_articles:
        negative_insight = _generate_sentiment_insight(
            negative_articles,
            sentiment_type="negative",
        )
        if negative_insight:
            insights.append(negative_insight)

    # 전체 요약 인사이트 생성 (LLM 사용)
    if len(relevant_results) >= 3:
        summary_insight = _generate_llm_summary_insight(relevant_results)
        if summary_insight:
            insights.append(summary_insight)

    logger.info("Generated insights count=%s", len(insights))
    return insights


def _generate_sentiment_insight(
    articles: list[dict[str, Any]],
    sentiment_type: str,
) -> dict[str, Any] | None:
    """감정 그룹별 인사이트를 생성한다.

    Args:
        articles (list[dict[str, Any]]): 감정 분석 결과 리스트.
        sentiment_type (str): "positive" 또는 "negative".

    Returns:
        dict[str, Any] | None: 생성된 인사이트. 없으면 None.
    """
    if not articles:
        return None

    avg_sentiment = sum(item.get("sentiment", 0.0) for item in articles) / len(articles)
    avg_relevance = sum(item.get("relevance", 0.0) for item in articles) / len(articles)

    # 제목과 발행사 추출
    titles = []
    publishers = set()
    for item in articles[:5]:  # 최대 5개만
        doc = item.get("document", {})
        title = doc.get("title", "")
        publisher = doc.get("publisher", "")
        if title:
            titles.append(title)
        if publisher:
            publishers.add(publisher)

    if sentiment_type == "positive":
        title = f"긍정적 시장 신호 감지 ({len(articles)}개 기사)"
        bullets = [
            f"평균 감정 점수: {avg_sentiment:.2f} (긍정)",
            f"관련 기사 수: {len(articles)}개",
            f"주요 발행사: {', '.join(list(publishers)[:3])}",
        ]
    else:
        title = f"부정적 시장 신호 감지 ({len(articles)}개 기사)"
        bullets = [
            f"평균 감정 점수: {avg_sentiment:.2f} (부정)",
            f"관련 기사 수: {len(articles)}개",
            f"주요 발행사: {', '.join(list(publishers)[:3])}",
        ]

    # 대표 기사 제목 추가
    if titles:
        bullets.append(f"주요 기사: {titles[0][:80]}...")

    insight = Insight(
        title=title,
        bullets=bullets,
        actionable=True,
        confidence=round(avg_relevance, 2),
    )

    return insight.model_dump()


def _generate_llm_summary_insight(articles: list[dict[str, Any]]) -> dict[str, Any] | None:
    """LLM을 사용하여 전체 요약 인사이트를 생성한다.

    Args:
        articles (list[dict[str, Any]]): 감정 분석 결과 리스트.

    Returns:
        dict[str, Any] | None: 생성된 인사이트. 실패 시 None.
    """
    # 기사 제목과 감정 정보 수집
    article_summaries = []
    for item in articles[:10]:  # 최대 10개만
        doc = item.get("document", {})
        title = doc.get("title", "")
        sentiment = item.get("sentiment", 0.0)
        relevance = item.get("relevance", 0.0)

        if title:
            sentiment_label = "긍정" if sentiment > 0.3 else "부정" if sentiment < -0.3 else "중립"
            article_summaries.append(f"- {title} (감정: {sentiment_label}, 관련도: {relevance:.2f})")

    if not article_summaries:
        return None

    # LLM 프롬프트 생성
    prompt = f"""다음은 금융 뉴스 기사들의 제목과 감정 분석 결과입니다:

{chr(10).join(article_summaries)}

위 기사들을 분석하여 다음 형식으로 요약해주세요:
1. 주요 주제 (1줄)
2. 시장 영향 (1줄)
3. 투자자 행동 제안 (1줄)

각 항목은 한 줄로 간결하게 작성하고, 불렛 포인트 형식으로 반환하세요."""

    try:
        response = completion(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()
        bullets = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]

        insight = Insight(
            title="전체 시장 동향 분석",
            bullets=bullets[:5],  # 최대 5개
            actionable=True,
            confidence=0.85,
        )

        return insight.model_dump()

    except Exception as exc:
        logger.info("LLM summary generation failed: %s", exc)
        return None


INSIGHT_TOOL = FunctionTool(func=generate_insights)
INSIGHT_MODEL = LiteLlm(model=settings.openai_model, tool_choice="required")

INSIGHT_AGENT = LlmAgent(
    name="finance_news_insight_agent",
    model=INSIGHT_MODEL,
    instruction=INSIGHT_PROMPT,
    tools=[INSIGHT_TOOL],
)

logger.info("Insight agent initialized.")
