"""공통 데이터 스키마 정의 모듈."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class NewsDoc(BaseModel):
    """뉴스 문서를 표현하는 스키마.

    Attributes:
        url (HttpUrl): 기사 URL.
        title (str): 기사 제목.
        publisher (str): 발행 매체 이름.
        published_at (datetime): 기사 발행 시각.
        readable_text (str | None): 정제된 본문 텍스트.
    """

    url: HttpUrl = Field(..., description="기사 URL")
    title: str = Field(..., description="기사 제목")
    publisher: str = Field(..., description="발행 매체 이름")
    published_at: datetime = Field(..., description="기사 발행 시각")
    readable_text: str | None = Field(None, description="정제된 본문 텍스트")


class SentimentScore(BaseModel):
    """감정 분석 결과를 표현하는 스키마.

    Attributes:
        sentiment (float): 감정 점수(-1에서 1 사이).
        relevance (float): 문서 관련도 점수(0에서 1 사이).
    """

    sentiment: float = Field(..., ge=-1.0, le=1.0, description="감정 점수")
    relevance: float = Field(..., ge=0.0, le=1.0, description="문서 관련도 점수")


class Insight(BaseModel):
    """실행 가능한 인사이트를 표현하는 스키마.

    Attributes:
        title (str): 인사이트 제목.
        bullets (list[str]): 핵심 요약 문장 리스트.
        actionable (bool): 실행 가능 여부 플래그.
        confidence (float): 인사이트 신뢰도(0에서 1 사이).
    """

    title: str = Field(..., description="인사이트 제목")
    bullets: list[str] = Field(default_factory=list, description="핵심 요약 문장")
    actionable: bool = Field(..., description="실행 가능 여부")
    confidence: float = Field(..., ge=0.0, le=1.0, description="인사이트 신뢰도")


__all__ = ["NewsDoc", "SentimentScore", "Insight"]
