"""크롤러 에이전트 A2A 서버 모듈."""

from __future__ import annotations

import warnings

import uvicorn
from a2a.types import AgentSkill

from agents.crawler_agent.crawler_agent import CRAWLER_AGENT
from agents.helpers.create_a2a_server import attach_http_health, create_agent_a2a_server
from common.settings import settings

warnings.filterwarnings("ignore", category=UserWarning)

CRAWLER_AGENT_PUBLIC_HOST = settings.crawler_agent_public_host
CRAWLER_AGENT_PUBLIC_PORT = settings.crawler_agent_public_port

app = create_agent_a2a_server(
    agent=CRAWLER_AGENT,
    name="Crawler Agent",
    description="Collect financial news metadata",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="crawler_agent",
            name="Crawler Agent",
            description="Collect financial news metadata",
            tags=["crawler", "financial", "news"],
            examples=[
                "Fetch financial news for query=tesla OR nvda and lookback_hours=24",
                "지난 12시간 동안 '반도체' 키워드 뉴스를 수집해줘",
            ],
        )
    ],
    public_host=CRAWLER_AGENT_PUBLIC_HOST,
    public_port=CRAWLER_AGENT_PUBLIC_PORT,
    sub_agents=[],
    deps_timeout_sec=1.2,
).build()

attach_http_health(
    app,
    app_name="Crawler Agent",
    version="0.1.0",
    sub_agents=[],
    deps_timeout_sec=1.2,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=CRAWLER_AGENT_PUBLIC_PORT)  # nosec
