"""감정 분석 에이전트 A2A 서버 모듈."""

from __future__ import annotations

import warnings

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import attach_http_health, create_agent_a2a_server
from agents.sentiment_agent.sentiment_agent import SENTIMENT_AGENT
from common.settings import settings

warnings.filterwarnings("ignore", category=UserWarning)

SENTIMENT_AGENT_PUBLIC_HOST = settings.sentiment_agent_public_host
SENTIMENT_AGENT_PUBLIC_PORT = settings.sentiment_agent_public_port

app = create_agent_a2a_server(
    agent=SENTIMENT_AGENT,
    name="Sentiment Agent",
    description="Analyze sentiment and financial relevance of news articles",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="sentiment_agent",
            name="Sentiment Agent",
            description="Analyze sentiment and financial relevance of news articles",
            tags=["sentiment", "analysis", "financial", "news"],
            examples=[
                "Analyze sentiment for the given articles",
                "기사 리스트의 감정과 관련도를 분석해줘",
            ],
        )
    ],
    public_host=SENTIMENT_AGENT_PUBLIC_HOST,
    public_port=SENTIMENT_AGENT_PUBLIC_PORT,
    sub_agents=[],
    deps_timeout_sec=1.2,
).build()

attach_http_health(
    app,
    app_name="Sentiment Agent",
    version="0.1.0",
    sub_agents=[],
    deps_timeout_sec=1.2,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SENTIMENT_AGENT_PUBLIC_PORT)  # nosec
