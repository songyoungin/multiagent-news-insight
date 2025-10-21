"""인사이트 생성 에이전트 A2A 서버 모듈."""

from __future__ import annotations

import warnings

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import attach_http_health, create_agent_a2a_server
from agents.insight_agent.insight_agent import INSIGHT_AGENT
from common.settings import settings

warnings.filterwarnings("ignore", category=UserWarning)

INSIGHT_AGENT_PUBLIC_HOST = settings.insight_agent_public_host
INSIGHT_AGENT_PUBLIC_PORT = settings.insight_agent_public_port

app = create_agent_a2a_server(
    agent=INSIGHT_AGENT,
    name="Insight Agent",
    description="Generate actionable insights from sentiment analysis results",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="insight_agent",
            name="Insight Agent",
            description="Generate actionable insights from sentiment analysis results",
            tags=["insight", "analysis", "financial", "news"],
            examples=[
                "Generate insights from the sentiment analysis results",
                "감정 분석 결과에서 인사이트를 생성해줘",
            ],
        )
    ],
    public_host=INSIGHT_AGENT_PUBLIC_HOST,
    public_port=INSIGHT_AGENT_PUBLIC_PORT,
    sub_agents=[],
    deps_timeout_sec=1.2,
).build()

attach_http_health(
    app,
    app_name="Insight Agent",
    version="0.1.0",
    sub_agents=[],
    deps_timeout_sec=1.2,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=INSIGHT_AGENT_PUBLIC_PORT)  # nosec
