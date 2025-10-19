import argparse
import asyncio
import inspect
import traceback
import warnings
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory, ClientCallContext
from google.adk.agents.run_config import RunConfig
from a2a.types import Message, Task, TextPart

from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)

warnings.filterwarnings("ignore", category=UserWarning)

ORCHESTRATOR_AGENT_URL = f"http://{settings.orchestrator_agent_public_host}:{settings.orchestrator_agent_public_port}"


def _collect_text_parts(items: Iterable[Any]) -> list[str]:
    """텍스트 파트를 안전하게 수집한다.

    Args:
        items: parts 속성을 가질 수 있는 객체 iterable.

    Returns:
        List[str]: 발견된 TextPart 텍스트 목록.
    """
    collected: list[str] = []
    for item in items:
        parts = getattr(item, "parts", None)
        if isinstance(parts, Iterable) and not isinstance(parts, (str, bytes)):
            for part in parts:
                root = getattr(part, "root", None)
                if isinstance(root, TextPart):
                    collected.append(root.text)
    return collected


async def run_orchestrator_agent(message: str, max_llm_calls: int = 5) -> None:
    logger.info(f"Connecting to agent at {ORCHESTRATOR_AGENT_URL}...")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(1200)) as httpx_client:
            card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=ORCHESTRATOR_AGENT_URL)
            card = await card_resolver.get_agent_card()
            client_config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=card)

            logger.info("Connected to agent successfully.")

            request = Message(messageId=str(uuid4()), role="user", parts=[TextPart(text=message)])

            context = ClientCallContext(run_config=RunConfig(max_llm_calls=max_llm_calls))
            result = client.send_message(request, context=context)
            
            if inspect.isasyncgen(result):
                # 스트리밍이면 마지막 이벤트(보통 최종 Task)를 결과로
                last_event = None
                async for ev in result:
                    last_event = ev
                task_or_tuple = last_event
            else:
                task_or_tuple = await result

            # (Task, None) 같은 튜플이면 첫 요소 사용
            task: Task = task_or_tuple[0] if isinstance(task_or_tuple, (tuple, list)) else task_or_tuple

            final_text = None
            artifacts_attr = getattr(task, "artifacts", None)
            if isinstance(artifacts_attr, Iterable) and not isinstance(artifacts_attr, (str, bytes)):
                text_chunks = _collect_text_parts(artifacts_attr)
                if text_chunks:
                    final_text = text_chunks[-1]

            if final_text is None:
                history_attr = getattr(task, "history", None)
                if isinstance(history_attr, Iterable) and not isinstance(history_attr, (str, bytes)):
                    for history_message in reversed(list(history_attr)):
                        text_chunks = _collect_text_parts([history_message])
                        if text_chunks:
                            final_text = text_chunks[-1]
                            break

            logger.info("Agent response:")
            logger.info(final_text or "Response text not found.")
            logger.info(f"Total tokens: {task.metadata.get('adk_usage_metadata')}")

    except Exception as e:
        traceback.print_exc()
        logger.error(f"--- An error occurred: {e} ---")
        logger.error("Ensure the agent server is running.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Agent Client (Google ADK Tool-Calling)")
    p.add_argument(
        "--command",
        help="자연어 명령. 예) '지난 24시간 동안 '테슬라 OR 엔비디아' 관련 뉴스 파이프라인을 실행해줘'",
        required=True,
    )
    p.add_argument(
        "--max-llm-calls",
        help="각 에이전트 내부에서 최대 LLM 호출 수. 기본값: 5",
        type=int,
        default=5,
    )
    args = p.parse_args()

    asyncio.run(run_orchestrator_agent(message=args.command, max_llm_calls=args.max_llm_calls))
