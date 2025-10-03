from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
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

    task_id: str
    device_name: str
    device_id: str
    task_type: str
    cron: str
    params: Dict[str, Any] = field(default_factory=dict)
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    error: Optional[str] = None

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

    def __init__(self, poll_interval: float = 1.0) -> None:
        self._poll_interval = poll_interval
        self._config = ServercConfig()
        self._handlers: Dict[str, TaskHandler] = {}
        self._tasks: List[ScheduledTask] = []
        self._tasks_by_id: Dict[str, ScheduledTask] = {}
        self._lock = threading.RLock()
        self._scheduler: Optional[BackgroundScheduler] = None
        self._running = False
        self._started_at: Optional[datetime] = None
        self.reload_tasks()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        """Register a callable to execute tasks of the given type."""

        with self._lock:
            self._handlers[task_type] = handler

    def start(self, *, reload_config: bool = False) -> None:
        """Start the daemon if it is not already running."""

        with self._lock:
            if self._running:
                raise DotDaemonError("Daemon is already running")
            if reload_config:
                self.reload_tasks()
            if not self._tasks:
                logger.warning("No tasks are configured; daemon will idle")
            scheduler = BackgroundScheduler()
            self._scheduler = scheduler
            self._apply_tasks_to_scheduler_locked(scheduler)
            self._running = True
            self._started_at = datetime.now()

        try:
            scheduler.start()
        except Exception:  # noqa: BLE001 - surface scheduler setup issues
            with self._lock:
                self._scheduler = None
                self._running = False
                self._started_at = None
            raise

        logger.info("DotDaemon started")

    def stop(self) -> None:
        """Stop the daemon if it is running."""

        with self._lock:
            if not self._running:
                logger.info("DotDaemon stop requested but daemon is not running")
                return
            scheduler = self._scheduler
            self._scheduler = None
            self._running = False
            self._started_at = None

        if scheduler is not None:
            scheduler.shutdown(wait=True)

        logger.info("DotDaemon stopped")

    def restart(self) -> None:
        """Restart the daemon, reloading configuration in the process."""

        self.stop()
        self.reload_tasks()
        self.start()

    def reload_tasks(self) -> None:
        """Reload cron tasks from the configuration file."""

        with self._lock:
            self._config.load_config()
            if not self._config.validate():
                raise DotDaemonError("Configuration validation failed")

            tasks: List[ScheduledTask] = []
            base_time = datetime.now()
            for device, schedule_index, schedule in self._config.iter_device_schedules():
                cron_expression = str(schedule.get("cron", "")).strip()
                task_type = str(schedule.get("type", "")).strip()
                params = schedule.get("params") or {}
                raw_identifier = device.get("device_id") or device.get("name")
                if raw_identifier:
                    device_identifier = str(raw_identifier)
                else:
                    device_identifier = f"device-{schedule_index}"

                if not cron_expression or not task_type:
                    task_id = f"{device_identifier}:{schedule_index}"
                    task = ScheduledTask(
                        task_id=task_id,
                        device_name=device.get("name", ""),
                        device_id=device.get("device_id", ""),
                        task_type=task_type or "unknown",
                        cron=cron_expression or "* * * * *",
                        params=params,
                    )
                    task.error = "Missing cron or type"
                    tasks.append(task)
                    continue

                task_id = f"{device_identifier}:{schedule_index}"
                task = ScheduledTask(
                    task_id=task_id,
                    device_name=device.get("name", "unknown device"),
                    device_id=str(device.get("device_id", "")),
                    task_type=task_type,
                    cron=cron_expression,
                    params=params,
                )
                task.compute_next_run(base_time)
                tasks.append(task)

            self._tasks = tasks
            self._tasks_by_id = {task.task_id: task for task in tasks}
            scheduler = self._scheduler
            if scheduler is not None:
                self._apply_tasks_to_scheduler_locked(scheduler)
            logger.info("Loaded %s scheduled tasks", len(tasks))

    def status(self) -> Dict[str, Any]:
        """Return a snapshot of the daemon state suitable for serialization."""

        with self._lock:
            tasks_status = [
                {
                    "task_id": task.task_id,
                    "device_name": task.device_name,
                    "device_id": task.device_id,
                    "type": task.task_type,
                    "cron": task.cron,
                    "params": task.params,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "error": task.error,
                }
                for task in self._tasks
            ]
            return {
                "running": self._running,
                "started_at": self._started_at.isoformat() if self._started_at else None,
                "task_count": len(self._tasks),
                "tasks": tasks_status,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_tasks_to_scheduler_locked(self, scheduler: BackgroundScheduler) -> None:
        scheduler.remove_all_jobs()
        for task in self._tasks:
            if task.error:
                continue
            try:
                trigger = CronTrigger.from_crontab(task.cron)
            except ValueError as exc:
                task.error = f"Invalid cron expression: {exc}"
                task.next_run = None
                continue
            job = scheduler.add_job(
                self._execute_task,
                trigger=trigger,
                id=task.task_id,
                replace_existing=True,
                args=[task.task_id],
            )
            task.next_run = job.next_run_time

    def _execute_task(self, task_id: str) -> None:
        reference = datetime.now()

        with self._lock:
            task = self._tasks_by_id.get(task_id)
            handler = self._handlers.get(task.task_type) if task is not None else None
            if task is not None:
                task.last_run = reference

        if task is None:
            logger.warning("Received execution request for unknown task '%s'", task_id)
            return

        try:
            if handler is not None:
                handler(task)
            else:
                logger.info("No handler registered for task type '%s'; skipping", task.task_type)
            error: Optional[str] = None
        except Exception as exc:  # noqa: BLE001 - surface handler issues
            logger.exception("Task %s failed", task.task_id)
            error = str(exc)
        finally:
            with self._lock:
                task.error = error
                scheduler = self._scheduler
                if scheduler is not None:
                    job = scheduler.get_job(task.task_id)
                    if job is not None:
                        task.next_run = job.next_run_time
                    else:
                        task.compute_next_run(reference)
                else:
                    task.compute_next_run(reference)


__all__ = ["DotDaemon", "DotDaemonError", "ScheduledTask"]
