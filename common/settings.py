"""애플리케이션 설정 모듈."""

from __future__ import annotations

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """환경 변수 기반 애플리케이션 설정을 관리한다.

    Attributes:
        azure_openai_deployment (str): Azure OpenAI 배포 이름.
        orchestrator_agent_public_host (str): 오케스트레이터 공개 호스트명.
        orchestrator_agent_public_port (int): 오케스트레이터 공개 포트.
        crawler_agent_url (HttpUrl): 크롤러 에이전트 카드 URL.
        parser_agent_url (HttpUrl): 파서 에이전트 카드 URL.
        cluster_agent_url (HttpUrl): 클러스터 에이전트 카드 URL.
        sentiment_agent_url (HttpUrl): 감정 에이전트 카드 URL.
        insight_agent_url (HttpUrl): 인사이트 에이전트 카드 URL.
    """

    model_config = SettingsConfigDict(env_prefix="MNI_", env_file=".env", extra="ignore")

    azure_openai_deployment: str = "gpt-4o-mini"
    orchestrator_agent_public_host: str = "127.0.0.1"
    orchestrator_agent_public_port: int = 8200

    crawler_agent_url: HttpUrl = "http://127.0.0.1:8201"
    parser_agent_url: HttpUrl = "http://127.0.0.1:8202"
    cluster_agent_url: HttpUrl = "http://127.0.0.1:8203"
    sentiment_agent_url: HttpUrl = "http://127.0.0.1:8204"
    insight_agent_url: HttpUrl = "http://127.0.0.1:8205"


settings = AppSettings()
