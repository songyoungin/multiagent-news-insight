# syntax=docker/dockerfile:1
FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY agents ./agents
COPY common ./common
COPY tools ./tools

# uv 설치 및 의존성 설치 (한 번에 실행)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    . /root/.local/bin/env && \
    uv sync --frozen --no-dev

ENV PATH="/root/.local/bin:${PATH}"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 헬스체크용 curl 유지
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8200}/health || exit 1

# 기본 실행 명령 (docker-compose에서 override됨)
CMD ["python", "-m", "agents.orchestrator_agent.orchestrator_server"]
