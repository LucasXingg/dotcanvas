import importlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from PIL import Image
import io
import base64


from .service_config import ServercConfig
from .api import APIClient


logger = logging.getLogger("dot.daemon")


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

    def __init__(self, config_path: str | Path | None = None) -> None:

        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"

        self.is_running = False

        self.config_path = config_path
        self.load_config()

        self.api_client = APIClient(key=self.config.get_api_key())

        self.scheduler = BackgroundScheduler()
        self.start()

    def load_config(self) -> None:
        self.config = ServercConfig(self.config_path)
        if not self.config.validate():
            raise DotDaemonError("Invalid configuration")
        
    def load_tasks(self) -> None:
        self.scheduler = BackgroundScheduler()
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
        if not self.scheduler.running:
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
        start_time = time.time()
        image = None
        try:
            canvas_module_name = f"canvas.{task.canvas_id}"
            canvas_file = Path(__file__).resolve().parents[1] / "canvas" / f"{task.canvas_id}.py"

            if not canvas_file.exists():
                raise FileNotFoundError(f"Canvas file not found for id '{task.canvas_id}'")

            module = importlib.import_module(canvas_module_name)

            canvas_class = getattr(module, "Canvas", None)
            render_callable = getattr(canvas_class, "render")

            image = render_callable()

            if image is None:
                raise ValueError(f"Canvas '{task.canvas_id}' returned no image")
            
            base64_image = self.image_to_base64(image)
            self.api_client.send_image(
                device_id=task.device_id,
                image=base64_image)

            task.last_run = datetime.now()
            task.compute_next_run(task.last_run)
        except Exception as exc:
            logger.error(f"Error executing task {task.task_name}: {exc}")
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Task {task.task_name} for device {task.device_name} completed. Duration: {duration:.2f} seconds")

    def image_to_base64(self, img: Image.Image, format: str = "PNG") -> str:
        # Create an in-memory buffer
        buffered = io.BytesIO()
        # Save the image into the buffer
        img.save(buffered, format=format)
        # Get the byte data
        img_bytes = buffered.getvalue()
        # Encode to base64
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        return img_b64



__all__ = ["DotDaemon", "DotDaemonError", "ScheduledTask"]
