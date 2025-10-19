"""애플리케이션 설정 모듈."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """환경 변수 기반 애플리케이션 설정을 관리한다.

    Attributes:
        openai_model (str): OpenAI에서 사용할 기본 모델 이름.
        orchestrator_agent_public_host (str): 오케스트레이터 공개 호스트명.
        orchestrator_agent_public_port (int): 오케스트레이터 공개 포트.
        crawler_agent_url (HttpUrl): 크롤러 에이전트 카드 URL.
        parser_agent_url (HttpUrl): 파서 에이전트 카드 URL.
        cluster_agent_url (HttpUrl): 클러스터 에이전트 카드 URL.
        sentiment_agent_url (HttpUrl): 감정 에이전트 카드 URL.
        insight_agent_url (HttpUrl): 인사이트 에이전트 카드 URL.
        newsapi_api_key (str | None): NewsAPI 인증 키.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_model: str = "openai/gpt-4o-mini"

    # 오케스트레이터 에이전트 공개 호스트 및 포트 정보
    orchestrator_agent_public_host: str = "0.0.0.0"
    orchestrator_agent_public_port: int = 8200

    # 크롤러 에이전트 공개 호스트 및 포트 정보
    crawler_agent_public_host: str = "0.0.0.0"
    crawler_agent_public_port: int = 8201

    # 파서 에이전트 공개 호스트 및 포트 정보
    parser_agent_public_host: str = "0.0.0.0"
    parser_agent_public_port: int = 8202

    # 클러스터 에이전트 공개 호스트 및 포트 정보
    cluster_agent_public_host: str = "0.0.0.0"
    cluster_agent_public_port: int = 8203

    # 감정 에이전트 공개 호스트 및 포트 정보
    sentiment_agent_public_host: str = "0.0.0.0"
    sentiment_agent_public_port: int = 8204

    # 인사이트 에이전트 공개 호스트 및 포트 정보
    insight_agent_public_host: str = "0.0.0.0"
    insight_agent_public_port: int = 8205

    # NewsAPI 인증 키
    newsapi_api_key: str | None = None


settings = AppSettings()
