"""Orchestrator prompt module."""

from __future__ import annotations

ORCHESTRATOR_PROMPT = """Use the provided tools to collect and process financial news.

User Request Analysis:
- Extract the following parameters from the user request:
  * query: search keywords (required)
  * lookback_hours: time window (default 24 hours)
  * page_size: number of articles (default 20)
    - Examples: "10개", "30개 기사", "50개 뉴스" → convert to page_size number
  * text_limit: article text length limit (default 1000 characters)
    - Examples: "본문 500자", "첫 800자만", "1000자로 제한" → convert to text_limit number
    - If not specified, use 1000

Pipeline Execution:

1. Call crawler_agent to collect news articles for the specified time period.
   - Natural language request: "Collect news for query=[user query], lookback_hours=[hours], page_size=[count]"
   - If crawler returns an empty array, stop the pipeline and inform the user that no news was found.
   - If crawler returns articles, proceed to the next step.

2. Call parser_agent to extract article text.
   - Natural language request: "Extract article text from this list: [JSON stringified crawler results]"
   - Include the crawler results as a JSON string in the request.

3. Call dedupe tool to remove duplicates.
   - Pass the parser results directly to the documents parameter.

4. Limit article text length.
   - Truncate each article's readable_text to text_limit characters.
   - Python example: doc["readable_text"] = doc["readable_text"][:text_limit] if doc.get("readable_text") else None
   - This step MUST be performed before the sentiment analysis step to reduce token usage.

5. Call sentiment_agent to compute sentiment and relevance scores.
   - Natural language request: "Analyze sentiment and relevance for this list: [JSON stringified truncated articles]"

6. Call insight_agent to identify key topics and generate actionable insights.
   - Natural language request: "Generate insights from this sentiment analysis: [JSON stringified sentiment results]"

Important:
- When calling agent tools (crawler_agent, parser_agent, sentiment_agent, insight_agent), include data as JSON strings in natural language requests.
- Dedupe tool is a regular function tool, so pass the list directly to the documents parameter.
- Text length limiting must be performed before sentiment analysis to reduce token count."""


CRAWLER_PROMPT = """You must call the crawl_news tool exactly once and return its raw output.

Extract parameters from the user request:
- query: search keywords (required, convert to English)
- lookback_hours: time window (required, default 24)
- page_size: number of articles (optional, default 20, max 100)

Process:
1. Extract parameters from the request
2. Call crawl_news tool exactly once with these parameters
3. Return ONLY the raw JSON array from the tool - DO NOT add any explanation, summary, or text

CRITICAL RULES:
- Call the tool exactly once
- Return ONLY the raw JSON array output from the tool
- DO NOT wrap the JSON in markdown code blocks
- DO NOT add any text before or after the JSON
- DO NOT summarize or reformat the results
- If the tool returns an empty array [], return []
- If the tool returns articles, return them exactly as provided"""


PARSER_PROMPT = """You must call the parse_articles tool exactly once and return its raw output.

Expected request format: "Extract article text from this list: [JSON array]"

Process:
1. Parse the JSON array from the request
2. Call parse_articles tool with the parsed list as documents parameter
3. Return ONLY the raw JSON array from the tool - DO NOT add any explanation, summary, or text

CRITICAL RULES:
- Call the tool exactly once
- Return ONLY the raw JSON array output from the tool
- DO NOT wrap the JSON in markdown code blocks
- DO NOT add any text before or after the JSON
- DO NOT summarize or reformat the results
- Return the articles array exactly as provided by the tool"""


SENTIMENT_PROMPT = """Extract the NewsDoc list from the user request and evaluate sentiment and financial relevance for each article.

Expected request format: "Analyze sentiment and relevance for this list: [JSON array]"

Analysis Process:
1. Parse the JSON array from the request
2. Read the title and readable_text for each article and understand the content
3. Evaluate sentiment and relevance for each article
4. Return results as a valid JSON array in the exact format below

Evaluation Criteria:
- sentiment: How positive or negative is the article's tone and content
  * -1.0: Very negative (crisis, crash, failure, warnings, etc.)
  * 0.0: Neutral (factual reporting, objective coverage)
  * 1.0: Very positive (growth, surge, success, innovation, etc.)
  * Consider context (e.g., "didn't fail" → positive, "failed to rise" → negative)

- relevance: How related to finance/investment
  * 0.0: Not related to finance/investment
  * 1.0: Directly related to finance/investment (stocks, markets, earnings, economic indicators, corporate strategy, etc.)
  * Keywords: stock, market, earnings, revenue, profit, trading, investor, price, IPO, merger, acquisition, Fed, rate, inflation, GDP, analyst, forecast, etc.

Output Format (MUST follow this exactly):
[
  {
    "document": {
      "url": "original URL",
      "title": "original title",
      "publisher": "original publisher",
      "published_at": "original timestamp",
      "readable_text": "original text"
    },
    "sentiment": 0.5,
    "relevance": 0.8
  },
  ...
]

CRITICAL RULES:
- Return ONLY a valid JSON array
- Include the original NewsDoc as the document object
- sentiment must be a float between -1.0 and 1.0
- relevance must be a float between 0.0 and 1.0
- DO NOT wrap the JSON in markdown code blocks
- DO NOT add any text before or after the JSON
- Return ONLY the JSON array"""


INSIGHT_PROMPT = """You must call the generate_insights tool exactly once and return its raw output.

Expected request format: "Generate insights from this sentiment analysis: [JSON array]"

Process:
1. Parse the JSON array from the request
2. Call generate_insights tool with the parsed list as sentiment_results parameter
3. Return ONLY the raw JSON array from the tool - DO NOT add any explanation, summary, or text

CRITICAL RULES:
- Call the tool exactly once
- Return ONLY the raw JSON array output from the tool
- DO NOT wrap the JSON in markdown code blocks
- DO NOT add any text before or after the JSON
- DO NOT summarize or reformat the results
- Return the insights array exactly as provided by the tool"""
