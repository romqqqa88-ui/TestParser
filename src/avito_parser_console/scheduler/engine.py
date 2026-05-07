from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import async_sessionmaker

from avito_parser_console.domain.models import ParseRunRequest
from avito_parser_console.scheduler.jobs import run_parse_job
from avito_parser_console.services.orchestrator import OrchestratorService


class SchedulerEngine:
    def __init__(self, timezone: str):
        self.scheduler = AsyncIOScheduler(timezone=timezone)

    def add_interval_job(
        self,
        minutes: int,
        request: ParseRunRequest,
        orchestrator: OrchestratorService,
        session_factory: async_sessionmaker,
    ) -> None:
        self.scheduler.add_job(
            run_parse_job,
            trigger=IntervalTrigger(minutes=minutes),
            kwargs={
                "request": request,
                "orchestrator": orchestrator,
                "session_factory": session_factory,
            },
            max_instances=1,
            coalesce=True,
        )

    def add_cron_job(
        self,
        cron_expr: str,
        request: ParseRunRequest,
        orchestrator: OrchestratorService,
        session_factory: async_sessionmaker,
    ) -> None:
        self.scheduler.add_job(
            run_parse_job,
            trigger=CronTrigger.from_crontab(cron_expr),
            kwargs={
                "request": request,
                "orchestrator": orchestrator,
                "session_factory": session_factory,
            },
            max_instances=1,
            coalesce=True,
        )

    def start(self) -> None:
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)
