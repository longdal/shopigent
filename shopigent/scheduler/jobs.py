import logging

logger = logging.getLogger(__name__)


async def run_search_task(task_id: int) -> None:
    """스케줄러가 호출하는 검색 태스크 실행 함수 (Phase 1에서 구현 예정)"""
    logger.info(f"태스크 {task_id} 실행 시작 (스케줄)")
    # TODO: Phase 1에서 agent.orchestrator.run_task(task_id) 호출로 교체
