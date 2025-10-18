## 프로젝트 개요

**multiagent-news-insight**
금융 뉴스를 자동으로 수집·분석·요약하여 **실행 가능한 인사이트**를 생성하는 멀티에이전트 시스템입니다.
초기 버전은 **Google ADK (A2A)** 기반으로 오케스트레이션되며, MCP는 후속 확장용으로 고려합니다.

---

## 주요 에이전트

| 에이전트                   | 역할                             | 입출력                                                            |
| ---------------------- | ------------------------------ | -------------------------------------------------------------- |
| **Orchestrator Agent** | 전체 파이프라인 제어 (수집→정제→군집→분석→인사이트) | 입력: `query`, `lookback_hours`<br>출력: 요약, 인사이트 리스트              |
| **Crawler Agent**      | 뉴스 API/RSS를 통해 기사 메타데이터 수집     | 입력: 검색어, 기간<br>출력: `url`, `title`, `publisher`, `published_at` |
| **Parser Agent**       | HTML 본문에서 읽기 가능한 텍스트 추출        | 입력: URL, HTML<br>출력: 정제된 본문 텍스트                                |
| **Dedupe Tool**        | 해시/유사도 기반 중복 제거 (툴 호출)        | 입력: 기사 리스트<br>출력: 고유 문서 목록                                     |
| **Cluster Agent**      | 문서 임베딩 기반 주제 군집화 및 토픽 라벨링      | 입력: 텍스트 리스트<br>출력: 클러스터 라벨, 핵심 키워드                             |
| **Sentiment Agent**    | 문서/클러스터별 감정·심리 점수 산출           | 입력: 텍스트<br>출력: 감정 스코어(-1~1), 관련도                               |
| **Insight Agent**      | 요약 및 인사이트 생성 (근거·리스크 포함)       | 입력: 클러스터/감정 결과<br>출력: 인사이트 문장, 신뢰도                             |

> Dedupe 단계는 독립 에이전트가 아닌 오케스트레이터가 호출하는 툴로 유지한다.

---

## 공통 데이터 스키마 (요약)

```python
class NewsDoc(BaseModel):
    url: HttpUrl
    title: str
    publisher: str
    published_at: datetime
    readable_text: Optional[str]

class SentimentScore(BaseModel):
    sentiment: float  # -1~1
    relevance: float  # 0~1

class Insight(BaseModel):
    title: str
    bullets: List[str]
    actionable: bool
    confidence: float
```

---

## 실행 플로우

```
Orchestrator
 ├─▶ Crawler → Parser → Dedupe Tool
 ├─▶ Cluster → Sentiment
 └─▶ Insight → 결과 통합
```

---

## 기술 스택

* **Frameworks:** FastAPI, Google ADK (A2A)
* **Data:** httpx, feedparser, trafilatura
* **ML/NLP:** sentence-transformers, transformers, torch
* **Logging & Tracing:** loguru, langfuse
* **Infra:** uvicorn, pydantic-settings

---

## 최소 API 예시

```bash
POST /orchestrate/run
# body: { "query": "tesla OR nvda", "lookback_hours": 24 }
# returns: { "summary": "...", "insights": [...] }
```

좋아요. 아래는 `agents.md` 마지막에 바로 추가할 수 있는 **최종 수정 버전**입니다.
`Optional[...]` 대신 `| None` 형식 사용 원칙까지 반영했습니다.

---

## 답변 및 코드 작성 규칙

### 1. 코드 작성 원칙

* **최소 변경 원칙(Minimal Change Rule)**
  기존 코드 구조를 불필요하게 변경하지 않는다. 수정은 명확한 개선이나 버그 수정에 한정한다.
* **도큐멘테이션**

  * 모든 함수에는 **Google Style 한글 Docstring**을 작성한다.
  * 주석은 **한글**로 작성한다.
  * **타입 힌트는 가능한 한 구체적으로 명시**한다.

    * 예시: `dict[str, str]`, `list[tuple[str, float]]`, `dict[str, Any] | None`
    * `Optional[...]` 대신 **PEP 604 형식 (`| None`)**을 사용할 것.
* **로깅 및 출력**

  * 로그 메시지(`loguru`, `logging`)는 **영어**로 작성한다.
  * `f-string` 대신 **lazy formatting**(`logger.info("... %s ...", variable)`)을 사용한다.
    이는 문자열 포맷 비용을 줄이고, 로그 레벨 필터링 시 불필요한 계산을 방지한다.
* **코드 예시**

  ```python
  from loguru import logger
  from typing import Any

  def fetch_news(query: str, params: dict[str, Any] | None = None) -> list[dict[str, str]]:
      """뉴스 API를 호출하여 기사 메타데이터를 반환한다.
      
      Args:
          query (str): 검색어 문자열.
          params (dict[str, Any] | None): 추가 요청 파라미터.
      
      Returns:
          list[dict[str, str]]: 기사 메타데이터 리스트.
      """
      logger.info("Fetching news for query: %s", query)
      ...
  ```

---

### 2. 답변 작성 원칙

* 모든 답변은 **한국어로 작성**한다.
* **불필요한 서론 없이 간결하게 핵심만 설명**한다.
* 코드 설명은 **변경 이유와 맥락만 요약**, 장황한 해설은 생략한다.
* 예시:

  > “`params` 인자의 타입을 `dict[str, Any] | None`으로 변경했습니다.
  > 로그 메시지는 lazy formatting을 사용하도록 수정했습니다.”
