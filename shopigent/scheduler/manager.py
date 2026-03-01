import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self):
        self._scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    def start(self) -> None:
        self._scheduler.start()
        logger.info("스케줄러 시작")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("스케줄러 종료")

    def add_periodic_task(self, task_id: int, cron_expression: str) -> None:
        """SearchTask ID와 cron 표현식으로 주기 작업 등록"""
        from shopigent.scheduler.jobs import run_search_task

        # cron_expression 예: "0 9 * * 1" (매주 월요일 09:00)
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"잘못된 cron 표현식: {cron_expression}")

        minute, hour, day, month, day_of_week = parts
        self._scheduler.add_job(
            run_search_task,
            "cron",
            id=f"task_{task_id}",
            args=[task_id],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            replace_existing=True,
        )
        logger.info(f"태스크 {task_id} 스케줄 등록: {cron_expression}")

    def remove_task(self, task_id: int) -> None:
        job_id = f"task_{task_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(f"태스크 {task_id} 스케줄 제거")

    @property
    def scheduler(self) -> AsyncIOScheduler:
        return self._scheduler


scheduler_manager = SchedulerManager()
