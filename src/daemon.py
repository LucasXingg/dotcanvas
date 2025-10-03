import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter

from .service_config import ServercConfig


logger = logging.getLogger(__name__)


TaskHandler = Callable[["ScheduledTask"], None]


@dataclass
class ScheduledTask:
    """Represents a single cron-based task loaded from the service config."""

    task_name: str
    device_name: str
    device_id: str
    cron: str
    canvas_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None

    def compute_next_run(self, reference: Optional[datetime] = None) -> None:
        reference_time = reference or datetime.now()
        try:
            iterator = croniter(self.cron, reference_time)
            self.next_run = iterator.get_next(datetime)
            self.error = None
        except ValueError as exc:  # croniter raises ValueError for invalid expressions
            self.error = f"Invalid cron expression: {exc}"
            self.next_run = None


class DotDaemonError(RuntimeError):
    """Raised when daemon control commands fail."""


class DotDaemon:
    """Background worker that executes configured tasks on a cron schedule."""

    def __init__(self, config_path: str | None = None) -> None:

        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"

        self.is_running = False

        self.config_path = config_path
        self.load_config()

        self.scheduler = BackgroundScheduler()

        self.load_tasks()
        self.start()

    def load_config(self) -> None:
        self.config = ServercConfig(self.config_path)
        if not self.config.validate():
            raise DotDaemonError("Invalid configuration")
        
    def load_tasks(self) -> None:
        for device, _, schedule in self.config.iter_device_schedules():
            try:
                task = ScheduledTask(
                    task_name=schedule["name"],
                    device_name=device["name"],
                    device_id=device["device_id"],
                    cron=schedule["cron"],
                    canvas_id=schedule["canvas_id"],
                    params=schedule.get("params", {}),
                )
                task.compute_next_run()

                self.scheduler.add_job(
                    self.canvas_executer,
                    trigger=CronTrigger.from_crontab(task.cron),
                    args=[task],
                    id=f"{device['device_id']}_{task.task_name}",
                    replace_existing=True,
                )
                
            except Exception as exc:
                logger.warning(f"Failed to load schedule for device {device.get('name', 'unknown')}: {exc}")

    def start(self) -> None:
        # If scheduler was shut down, create a new one
        if not self.scheduler or not self.scheduler.running:
            # If the executor pool is dead, APScheduler will not restart
            # So we just recreate a fresh scheduler
            if getattr(self.scheduler, "_stopped", False):  # internal flag after shutdown
                self.scheduler = BackgroundScheduler()
                self.load_tasks()

            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started")
        else:
            logger.info("Scheduler already running")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")

    def restart(self) -> None:
        self.stop()
        self.load_config()
        self.empty_tasks()
        self.load_tasks()
        self.start()

    def get_status(self) -> Dict[str, Any]:
        jobs = self.scheduler.get_jobs()
        tasks_info = []
        for job in jobs:
            task_info = {
                "id": job.id,
                "next_run": job.next_run_time,
            }
            tasks_info.append(task_info)
        return {
            "running": self.is_running,
            "task_count": len(jobs),
            "tasks": tasks_info,
        }

    def empty_tasks(self) -> None:
        self.scheduler.remove_all_jobs()
        logger.info("All scheduled tasks have been removed")

    def canvas_executer(self, task: ScheduledTask) -> None:
        logger.info(f"Executing task {task.task_name} for device {task.device_name}")


__all__ = ["DotDaemon", "DotDaemonError", "ScheduledTask"]
