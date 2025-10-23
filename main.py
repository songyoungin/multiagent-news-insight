import argparse
import asyncio
import inspect
import traceback
import warnings
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientCallContext, ClientConfig, ClientFactory
from a2a.types import Message, Task, TextPart
from google.adk.agents.run_config import RunConfig

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
            client_config = ClientConfig(httpx_client=httpx_client, streaming=True)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=card)

            logger.info("Connected to agent successfully.")

            request = Message(messageId=str(uuid4()), role="user", parts=[TextPart(text=message)])

            context = ClientCallContext(run_config=RunConfig(max_llm_calls=max_llm_calls))
            result = client.send_message(request, context=context)

            logger.info("=" * 80)
            logger.info("🔄 Streaming events from orchestrator:")
            logger.info("=" * 80)

            if inspect.isasyncgen(result):
                # 스트리밍이면 각 이벤트를 실시간으로 출력
                last_event = None
                event_count = 0
                async for ev in result:
                    event_count += 1
                    last_event = ev

                    # 튜플이면 첫 번째 요소가 Task
                    task_event = ev[0] if isinstance(ev, (tuple, list)) else ev

                    # 이벤트 타입 확인
                    logger.info(f"\n📦 Event #{event_count}: type={type(task_event).__name__}")

                    # Task 객체인 경우
                    if hasattr(task_event, "history"):
                        history = getattr(task_event, "history", [])
                        if history:
                            history_list = list(history)
                            logger.info(f"   📜 History length: {len(history_list)}")

                            if history_list:
                                last_msg = history_list[-1]

                                # 메시지 구조 디버깅
                                logger.info(f"   🔍 Last message type: {type(last_msg).__name__}")
                                logger.info(f"   🔍 Last message role: {getattr(last_msg, 'role', 'N/A')}")

                                # parts 직접 확인
                                parts = getattr(last_msg, "parts", None)
                                if parts:
                                    logger.info(f"   🔍 Parts type: {type(parts).__name__}")
                                    parts_list = list(parts) if parts else []
                                    logger.info(f"   🔍 Parts count: {len(parts_list)}")

                                    # 각 part 확인
                                    for i, part in enumerate(parts_list):
                                        logger.info(f"   🔍 Part #{i} type: {type(part).__name__}")

                                        # Part 객체의 모든 속성 출력
                                        logger.info(f"   📋 Part #{i} dir(): {dir(part)}")

                                        # __dict__ 확인
                                        if hasattr(part, "__dict__"):
                                            logger.info(f"   📋 Part #{i} __dict__: {part.__dict__}")

                                        # vars() 확인
                                        try:
                                            logger.info(f"   📋 Part #{i} vars(): {vars(part)}")
                                        except TypeError:
                                            logger.info(f"   📋 Part #{i} vars(): Not available")

                                        # repr 확인
                                        logger.info(f"   📋 Part #{i} repr: {repr(part)}")

                                        # str 확인
                                        logger.info(f"   📋 Part #{i} str: {str(part)}")

                                        # TextPart 확인
                                        if hasattr(part, "text"):
                                            text = getattr(part, "text", None)
                                            if text:
                                                preview = text[:300] if len(text) > 300 else text
                                                logger.info(f"   💬 Part #{i} text preview:\n{preview}...")

                                                # JSON 배열인지 확인
                                                if text.strip().startswith("["):
                                                    logger.info(f"   ✅ Part #{i} looks like JSON array response")

                                        # root 속성 확인 (원래 로직)
                                        root = getattr(part, "root", None)
                                        if root:
                                            logger.info(f"   📋 Part #{i} root type: {type(root).__name__}")
                                            logger.info(f"   📋 Part #{i} root dir(): {dir(root)}")
                                            if hasattr(root, "__dict__"):
                                                logger.info(f"   📋 Part #{i} root.__dict__: {root.__dict__}")

                                            if hasattr(root, "text"):
                                                text = getattr(root, "text", None)
                                                if text:
                                                    preview = text[:300] if len(text) > 300 else text
                                                    logger.info(f"   💬 Part #{i} root.text preview:\n{preview}...")
                                else:
                                    logger.info(f"   ⚠️ No parts found in message")

                    # Artifact 확인
                    if hasattr(task_event, "artifacts"):
                        artifacts = getattr(task_event, "artifacts", None)
                        if artifacts is not None:
                            try:
                                artifacts_list = list(artifacts)
                                if artifacts_list:
                                    logger.info(f"   📎 Artifacts count: {len(artifacts_list)}")
                            except TypeError:
                                pass  # artifacts가 iterable하지 않은 경우

                    # State 확인 (진행 상태)
                    if hasattr(task_event, "state"):
                        state = getattr(task_event, "state", None)
                        if state:
                            logger.info(f"   🔵 Task state: {state}")

                logger.info("=" * 80)
                logger.info(f"✅ Streaming completed: {event_count} events received")
                logger.info("=" * 80)
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
