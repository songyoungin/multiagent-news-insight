# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**multiagent-news-insight** is a multi-agent system that collects, analyzes, and summarizes financial news to generate actionable market insights. The system uses Google ADK (A2A - Agent-to-Agent) protocol for orchestration.

## Tech Stack

- **Framework**: FastAPI, Google ADK (A2A protocol)
- **Data Collection**: httpx, newsapi-python, trafilatura
- **ML/NLP**: (optional) sentence-transformers, transformers
- **LLM**: LiteLLM (supports OpenAI models via `openai/gpt-4o-mini` format)
- **Logging**: loguru
- **Python**: 3.13+
- **Package Manager**: uv

## Development Commands

### Setup
```bash
# Create virtual environment and install dependencies
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY and NEWSAPI_API_KEY
```

### Running Agents

Each agent runs as a separate server on its own port (configured in `.env`):

```bash
# Run orchestrator agent (port 8200 by default)
uv run python -m agents.orchestrator_agent.orchestrator_server

# Run crawler agent (port 8201 by default)
uv run python -m agents.crawler_agent.crawler_server

# Run parser agent (port 8202 by default)
uv run python -m agents.parser_agent.parser_server

# Run sentiment agent (port 8203 by default)
uv run python -m agents.sentiment_agent.sentiment_server

# Run insight agent (port 8204 by default)
uv run python -m agents.insight_agent.insight_server
```

### Client Usage

```bash
# Execute a news analysis pipeline
uv run python main.py --command "지난 24시간 동안 'tesla OR nvidia' 관련 뉴스 파이프라인을 실행해줘" --max-llm-calls 5
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

## Architecture

### Multi-Agent Pipeline

The system follows a simplified pipeline architecture orchestrated by the Orchestrator Agent:

```
User Request → Orchestrator Agent
                    ↓
                Crawler Agent (collects news metadata)
                    ↓
                Parser Agent (extracts article text)
                    ↓
                Dedupe Tool (removes duplicates)
                    ↓
                Sentiment Agent (analyzes sentiment & relevance)
                    ↓
                Insight Agent (identifies topics & generates insights)
                    ↓
                Final Report
```

### Agent Communication (A2A Protocol)

- Each agent is an independent FastAPI server exposing A2A endpoints
- Agents communicate via HTTP using Google ADK's A2A protocol
- Agent cards are exposed at `http://host:port/.well-known/agent-card.json`
- The Orchestrator uses `RemoteA2aAgent` to call sub-agents
- Sub-agents use `FunctionTool` to wrap Python functions

### Key Components

#### 1. Agents (`agents/`)
Each agent has its own directory with:
- `*_agent.py`: Agent definition with LLM model, prompt, and tools
- `*_server.py`: FastAPI server that exposes the agent via A2A protocol
- Agent initialization happens in `__init__.py`

#### 2. Common Utilities (`common/`)
- `schemas.py`: Shared Pydantic models (`NewsDoc`, `SentimentScore`, `Insight`)
- `prompts.py`: System prompts for each agent
- `settings.py`: Environment-based configuration using `pydantic-settings`
- `logger.py`: loguru-based logging setup
- `telemetry.py`: Langfuse instrumentation

#### 3. Tools (`tools/`)
- `dedupe_tool.py`: Deduplication tool called by orchestrator
- Tools are wrapped with `FunctionTool` for ADK integration

#### 4. Helpers (`agents/helpers/`)
- `create_a2a_server.py`: Factory functions for creating A2A servers
  - `create_agent_a2a_server()`: Creates A2A server with health checks
  - `attach_http_health()`: Adds HTTP `/health` endpoint
  - `HealthAwareRequestHandler`: Custom handler supporting `health.ping` JSON-RPC method
  - `SubAgent`: Represents sub-agent dependencies for health checks

### Data Flow

1. **Crawler Agent**: Calls NewsAPI to fetch article metadata (URL, title, publisher, published_at)
2. **Parser Agent**: Extracts readable text from HTML using trafilatura
3. **Dedupe Tool**: Removes duplicate articles (hash/similarity-based)
4. **Sentiment Agent**: Computes sentiment scores (-1 to 1) and relevance (0 to 1) for each article
5. **Insight Agent**: Identifies key topics and generates actionable insights with confidence scores

### Configuration

All configuration is managed via environment variables (`.env`):
- `OPENAI_MODEL`: LLM model in format `provider/model` (e.g., `openai/gpt-4o-mini`)
- `OPENAI_API_KEY`: OpenAI API key for LLM calls
- `NEWSAPI_API_KEY`: NewsAPI key for article collection
- `*_AGENT_PUBLIC_HOST` / `*_AGENT_PUBLIC_PORT`: Network settings for each agent

## Code Style Guidelines

### Language and Documentation
- **Docstrings**: Google Style in Korean
- **Comments**: Korean
- **Log messages**: English
- **Code**: English (variable names, function names, etc.)

### Type Hints
- Always use specific type hints: `dict[str, str]`, `list[tuple[str, float]]`
- Use PEP 604 syntax: `str | None` instead of `Optional[str]`
- Avoid generic types without parameters

### Logging
- Use lazy formatting: `logger.info("Message %s", variable)` instead of f-strings
- This avoids string formatting overhead when logs are filtered by level

### Code Change Philosophy
- **Minimal Change Rule**: Only modify code when there's a clear bug fix or improvement
- Don't refactor unnecessarily

### Example
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

## Important Notes

### Agent Initialization Pattern
- Each agent module (`*_agent.py`) initializes its agent at module load time
- The agent is then imported and used by the server module (`*_server.py`)
- Server modules use `create_agent_a2a_server()` to wrap the agent with A2A protocol

### Health Checks
- Agents support both A2A JSON-RPC `health.ping` and HTTP `/health`
- Orchestrator can check sub-agent health with `include_dependencies=true`
- Health responses include: status, version, uptime_sec, latency_ms

### LLM Tool Calling
- Orchestrator uses `tool_choice="auto"` to let LLM decide when to call tools
- Sub-agents use `tool_choice="required"` to ensure they always call their function
- Tools return JSON-serializable results for agent communication