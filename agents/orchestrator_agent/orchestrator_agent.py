"""Google ADK 기반 오케스트레이터 에이전트 초기화 모듈."""

from __future__ import annotations

from google.adk.agents import ParallelAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from common.logger import get_logger
from common.prompts import ORCHESTRATOR_PROMPT
from common.settings import settings
from common.telemetry import instrument_langfuse
from tools.dedupe_tool import create_dedupe_tool

logger = get_logger(__name__)


def _build_agent_card_url(base_url: str) -> str:
    """에이전트 카드 URL을 생성한다.

    Args:
        base_url (str): 공개된 에이전트 베이스 URL.

    Returns:
        str: well-known 경로가 포함된 카드 URL.
    """
    normalized = base_url.rstrip("/")
    return f"{normalized}/{AGENT_CARD_WELL_KNOWN_PATH}"


AZURE_DEPLOYMENT = settings.azure_openai_deployment
LLM_MODEL = LiteLlm(model=f"azure/{AZURE_DEPLOYMENT}", tool_choice="auto")

CRAWLER_AGENT = RemoteA2aAgent(
    name="crawler_agent",
    description="Collect financial news metadata within a given lookback window.",
    agent_card=_build_agent_card_url(str(settings.crawler_agent_url)),
)
PARSER_AGENT = RemoteA2aAgent(
    name="parser_agent",
    description="Extract readable article text from HTML documents.",
    agent_card=_build_agent_card_url(str(settings.parser_agent_url)),
)
CLUSTER_AGENT = RemoteA2aAgent(
    name="cluster_agent",
    description="Cluster financial news documents into coherent themes.",
    agent_card=_build_agent_card_url(str(settings.cluster_agent_url)),
)
SENTIMENT_AGENT = RemoteA2aAgent(
    name="sentiment_agent",
    description="Compute sentiment and relevance scores for each cluster.",
    agent_card=_build_agent_card_url(str(settings.sentiment_agent_url)),
)
INSIGHT_AGENT = RemoteA2aAgent(
    name="insight_agent",
    description="Generate actionable insights grounded in clustered documents.",
    agent_card=_build_agent_card_url(str(settings.insight_agent_url)),
)

CRAWLER_AGENT_TOOL = AgentTool(CRAWLER_AGENT)
PARSER_AGENT_TOOL = AgentTool(PARSER_AGENT)
CLUSTER_SENTIMENT_PARALLEL_AGENT = ParallelAgent(
    name="analysis_parallel_agent",
    description="Run clustering and sentiment extraction in parallel for efficiency.",
    sub_agents=[
        CLUSTER_AGENT,
        SENTIMENT_AGENT,
    ],
)
CLUSTER_SENTIMENT_TOOL = AgentTool(CLUSTER_SENTIMENT_PARALLEL_AGENT)
INSIGHT_AGENT_TOOL = AgentTool(INSIGHT_AGENT)

instrument_langfuse()

try:
    DEDUPE_TOOL = create_dedupe_tool()
except RuntimeError as exc:
    logger.info("Dedupe tool initialization failed: %s", exc)
    DEDUPE_TOOL = None

TOOLING = [
    CRAWLER_AGENT_TOOL,
    PARSER_AGENT_TOOL,
    CLUSTER_SENTIMENT_TOOL,
    INSIGHT_AGENT_TOOL,
]
if DEDUPE_TOOL is not None:
    TOOLING.insert(2, DEDUPE_TOOL)

ORCHESTRATOR_AGENT = LlmAgent(
    name="finance_news_orchestrator_agent",
    model=LLM_MODEL,
    instruction=ORCHESTRATOR_PROMPT,
    tools=TOOLING,
)
logger.info("Orchestration agent initialized.")
