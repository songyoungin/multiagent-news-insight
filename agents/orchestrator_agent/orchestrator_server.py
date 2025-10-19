import warnings

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import attach_http_health, create_agent_a2a_server
from agents.orchestrator_agent.orchestrator_agent import ORCHESTRATOR_AGENT
from common.settings import settings

warnings.filterwarnings("ignore", category=UserWarning)

ORCHESTRATOR_AGENT_PUBLIC_HOST = settings.orchestrator_agent_public_host
ORCHESTRATOR_AGENT_PUBLIC_PORT = settings.orchestrator_agent_public_port

# 서브 에이전트 정보
SUB_AGENTS = []

# 오케스트레이션 에이전트 A2A 서버 생성
app = create_agent_a2a_server(
    agent=ORCHESTRATOR_AGENT,
    name="Orchestrator Agent",
    description="Orchestrate the financial news analysis pipeline",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="orchestrator_agent",
            name="Orchestrator Agent",
            description="Orchestrate the financial news analysis pipeline",
            tags=["orchestration", "financial", "news"],
            examples=[
                "지난 24시간 동안 '테슬라 OR 엔비디아' 관련 뉴스 파이프라인을 실행해줘.",
                "48시간 이내 은행 섹터 주요 뉴스를 요약하고 인사이트를 만들어줘.",
                "Run the news pipeline for query=tesla OR nvda within the last 24 hours.",
                "Summarize banking sector headlines from the past two days and produce actionable insights.",
            ],
        )
    ],
    public_host=ORCHESTRATOR_AGENT_PUBLIC_HOST,
    public_port=ORCHESTRATOR_AGENT_PUBLIC_PORT,
    sub_agents=SUB_AGENTS,
    deps_timeout_sec=1.2,
).build()

# HTTP /health 처리
attach_http_health(
    app,
    app_name="Orchestrator Agent",
    version="0.1.0",
    sub_agents=SUB_AGENTS,
    deps_timeout_sec=1.2,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=ORCHESTRATOR_AGENT_PUBLIC_PORT)  # nosec
