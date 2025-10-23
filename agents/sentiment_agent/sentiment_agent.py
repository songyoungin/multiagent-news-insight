"""감정 분석 에이전트 구성 모듈."""

from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from common.logger import get_logger
from common.prompts import SENTIMENT_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse

logger = get_logger(__name__)

instrument_langfuse()

SENTIMENT_MODEL = LiteLlm(model=settings.openai_model)

SENTIMENT_AGENT = LlmAgent(
    name="finance_news_sentiment_agent",
    model=SENTIMENT_MODEL,
    instruction=SENTIMENT_PROMPT,
    tools=[],
)

logger.info("Sentiment agent initialized.")
