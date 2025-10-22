"""오케스트레이터 프롬프트 모듈."""

from __future__ import annotations

ORCHESTRATOR_PROMPT = """주어진 툴을 사용해 금융 뉴스를 수집하고 정제하라.

1. 크롤러 에이전트를 호출하여 지정된 기간의 뉴스를 수집한다.
   - 자연어 요청: "query=[사용자 쿼리], lookback_hours=[시간] 조건으로 뉴스를 수집해줘"
   - 뉴스 검색 결과가 비어있을 경우, 이후 단계를 실행하지 말고 종료하라.

2. 파서 에이전트를 호출하여 본문을 추출한다.
   - 자연어 요청: "다음 기사 리스트에서 본문을 추출해줘: [크롤러 결과를 JSON 문자열로 변환]"
   - 크롤러 결과를 JSON.stringify() 형태로 포함시켜야 한다.

3. Dedupe 툴로 중복을 제거한다.
   - 파서 결과를 직접 전달한다.

4. 감정 분석 에이전트를 호출하여 각 기사의 감정과 관련도를 산출한다.
   - 자연어 요청: "다음 기사 리스트의 감정과 관련도를 분석해줘: [파서 결과를 JSON 문자열로 변환]"

5. 인사이트 에이전트를 호출하여 주요 주제를 파악하고 실행 가능한 인사이트를 정리한다.
   - 자연어 요청: "다음 감정 분석 결과로부터 인사이트를 생성해줘: [감정 분석 결과를 JSON 문자열로 변환]"

중요:
- 에이전트 툴(crawler_agent, parser_agent, sentiment_agent, insight_agent)을 호출할 때는 자연어 요청(request)에 데이터를 JSON 문자열로 포함시켜야 한다.
- Dedupe 툴은 일반 함수 툴이므로 documents 파라미터에 리스트를 직접 전달한다."""


CRAWLER_PROMPT = """사용자 요청을 분석하여 crawl_news 툴을 호출하라.

요청에서 다음 파라미터를 추출한다:
- query: 검색어 (필수, 영어로 변환)
- lookback_hours: 조회 기간 (필수, 기본값 24)
- page_size: 페이지당 기사 수 (선택, 기본값 20)

crawl_news 툴을 호출하여 NewsDoc 리스트를 반환하라.
query는 반드시 영어로 작성하라."""


PARSER_PROMPT = """사용자 요청에서 NewsDoc 리스트를 추출하여 parse_articles 툴을 호출하라.

요청 형식 예시: "다음 기사 리스트에서 본문을 추출해줘: [JSON 배열]"

1. 요청에서 JSON 배열을 파싱한다.
2. parse_articles 툴의 documents 파라미터에 파싱된 리스트를 전달한다.
3. 툴 호출 결과를 그대로 반환하라.

parse_articles는 NewsDoc 리스트를 입력받아 readable_text를 채운 NewsDoc 리스트를 반환한다."""


SENTIMENT_PROMPT = """사용자 요청에서 NewsDoc 리스트를 추출하여 analyze_sentiment 툴을 호출하라.

요청 형식 예시: "다음 기사 리스트의 감정과 관련도를 분석해줘: [JSON 배열]"

1. 요청에서 JSON 배열을 파싱한다.
2. analyze_sentiment 툴의 documents 파라미터에 파싱된 리스트를 전달한다.
3. 툴 호출 결과를 그대로 반환하라.

analyze_sentiment는 NewsDoc 리스트를 입력받아 각 기사의 감정 점수(-1~1)와 관련도(0~1)를 포함한 결과 리스트를 반환한다."""


INSIGHT_PROMPT = """사용자 요청에서 감정 분석 결과 리스트를 추출하여 generate_insights 툴을 호출하라.

요청 형식 예시: "다음 감정 분석 결과로부터 인사이트를 생성해줘: [JSON 배열]"

1. 요청에서 JSON 배열을 파싱한다.
2. generate_insights 툴의 sentiment_results 파라미터에 파싱된 리스트를 전달한다.
3. 툴 호출 결과를 그대로 반환하라.

generate_insights는 감정 분석 결과 리스트를 입력받아 실행 가능한 인사이트 리스트를 반환한다."""
