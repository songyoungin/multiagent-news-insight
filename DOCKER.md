# Docker 사용 가이드

이 문서는 Docker Compose를 사용하여 모든 에이전트를 실행하는 방법을 설명합니다.

## 사전 요구사항

- Docker Engine 20.10 이상
- Docker Compose V2 이상
- `.env` 파일에 필수 API 키 설정

## 환경 설정

1. `.env` 파일 생성 (`.env.example` 참고)

```bash
cp .env.example .env
```

2. 필수 환경 변수 설정

```bash
# .env 파일
OPENAI_API_KEY=your_openai_api_key_here
NEWSAPI_API_KEY=your_newsapi_key_here
OPENAI_MODEL=openai/gpt-4o-mini
```

## 실행 방법

### 1. 모든 서비스 시작

```bash
docker-compose up -d
```

이 명령은 다음 5개의 에이전트를 백그라운드에서 실행합니다:
- Orchestrator Agent (포트 8200)
- Crawler Agent (포트 8201)
- Parser Agent (포트 8202)
- Sentiment Agent (포트 8203)
- Insight Agent (포트 8204)

### 2. 서비스 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f orchestrator
```

### 3. 헬스 체크

```bash
# Orchestrator
curl http://localhost:8200/health

# Crawler
curl http://localhost:8201/health

# Parser
curl http://localhost:8202/health

# Sentiment
curl http://localhost:8203/health

# Insight
curl http://localhost:8204/health
```

### 4. 서비스 중지

```bash
# 모든 서비스 중지
docker-compose down

# 컨테이너와 볼륨 모두 삭제
docker-compose down -v
```

## 클라이언트 실행

에이전트 서버가 모두 실행 중인 상태에서:

```bash
# 로컬에서 클라이언트 실행
uv run python main.py --command "지난 24시간 동안 'tesla OR nvidia' 관련 뉴스 파이프라인을 실행해줘" --max-llm-calls 10
```

또는 Docker 컨테이너 내부에서 실행:

```bash
docker-compose exec orchestrator python main.py --command "..."
```

## 개별 서비스 재시작

```bash
# 특정 서비스만 재시작
docker-compose restart orchestrator

# 특정 서비스 재빌드 후 재시작
docker-compose up -d --build orchestrator
```

## 문제 해결

### 포트 충돌

이미 8200-8204 포트를 사용 중이라면:

```bash
# 사용 중인 포트 확인
lsof -i :8200-8204

# 프로세스 종료
kill <PID>
```

### 이미지 재빌드

코드를 수정한 경우 이미지를 재빌드해야 합니다:

```bash
docker-compose build
docker-compose up -d
```

또는 한 번에:

```bash
docker-compose up -d --build
```

### 로그 디버깅

특정 서비스의 자세한 로그:

```bash
docker-compose logs --tail=100 -f sentiment
```

### 컨테이너 셸 접속

```bash
docker-compose exec orchestrator /bin/bash
```

## 네트워크 구조

모든 에이전트는 `agent-network`라는 브리지 네트워크에 연결됩니다:

- 컨테이너 간 통신: 컨테이너 이름으로 접근 (예: `http://crawler:8201`)
- 호스트에서 접근: `http://localhost:8200-8204`

## 프로덕션 배포 시 고려사항

1. **환경 변수 보안**
   - `.env` 파일을 Git에 커밋하지 마세요
   - 프로덕션에서는 Docker Secrets 또는 환경 변수 관리 도구 사용

2. **리소스 제한**
   - `docker-compose.yml`에 CPU/메모리 제한 추가:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

3. **헬스 체크**
   - 모든 서비스에 헬스 체크가 구성되어 있습니다
   - `docker-compose ps`로 상태 확인

4. **로그 관리**
   - 로그 드라이버 설정:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

5. **퍼시스턴스**
   - 현재는 stateless 구조
   - 필요 시 볼륨 마운트 추가
