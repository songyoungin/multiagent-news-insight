"""파서 에이전트 A2A 서버 모듈."""

from __future__ import annotations

import warnings

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import attach_http_health, create_agent_a2a_server
from agents.parser_agent.parser_agent import PARSER_AGENT
from common.settings import settings

warnings.filterwarnings("ignore", category=UserWarning)

PARSER_AGENT_PUBLIC_HOST = settings.parser_agent_public_host
PARSER_AGENT_PUBLIC_PORT = settings.parser_agent_public_port

app = create_agent_a2a_server(
    agent=PARSER_AGENT,
    name="Parser Agent",
    description="Extract readable text from news article URLs",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="parser_agent",
            name="Parser Agent",
            description="Extract readable text from news article URLs",
            tags=["parser", "text-extraction", "news"],
            examples=[
                "Extract article text from the given URLs",
                "URL 목록에서 본문 텍스트를 추출해줘",
            ],
        )
    ],
    public_host=PARSER_AGENT_PUBLIC_HOST,
    public_port=PARSER_AGENT_PUBLIC_PORT,
    sub_agents=[],
    deps_timeout_sec=1.2,
).build()

attach_http_health(
    app,
    app_name="Parser Agent",
    version="0.1.0",
    sub_agents=[],
    deps_timeout_sec=1.2,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PARSER_AGENT_PUBLIC_PORT)  # nosec
