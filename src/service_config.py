from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import yaml


class ServercConfig:

    DEFAULT_PATH = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else self.DEFAULT_PATH
        self.cfg: Dict[str, Any] = {}
        self.load_config()


    def load_config(self) -> Dict[str, Any]:
        if not self.path.exists():
            msg = f"Config file not found: {self.path}"
            raise FileNotFoundError(msg)
        with self.path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            msg = "Configuration root must be a mapping"
            raise ValueError(msg)
        self.cfg = data
        return self.cfg


    def validate(self) -> bool:
        errors = []

        if not self.cfg.get("api_key"):
            errors.append("api_key is missing")

        devices = self.cfg.get("devices")
        if not devices:
            errors.append("devices is missing or empty")
        else:
            for idx, device in enumerate(devices, 1):
                if not isinstance(device, dict):
                    errors.append(f"device[{idx}] must be a mapping")
                    continue
                if not device.get("name"):
                    errors.append(f"device[{idx}].name is missing")
                if not device.get("device_id"):
                    errors.append(f"device[{idx}].device_id is missing")
                schedules = device.get("schedules")
                if schedules is None:
                    continue
                if not isinstance(schedules, list):
                    errors.append(f"device[{idx}].schedules must be a list")
                    continue
                for sidx, schedule in enumerate(schedules, 1):
                    if not isinstance(schedule, dict):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}] must be a mapping"
                        )
                        continue
                    if not schedule.get("cron"):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].cron is missing"
                        )
                    if not schedule.get("type"):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].type is missing"
                        )
                    if schedule.get("params") is None:
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].params is missing"
                        )

        if errors:
            print("Validation FAILED:")
            for error in errors:
                print(f" - {error}")
            return False
        print("Validation OK: no obvious errors found")
        return True


    def iter_device_schedules(self) -> Iterator[Tuple[Dict[str, Any], int, Dict[str, Any]]]:
        devices = self.cfg.get("devices") or []
        for device in devices:
            schedules = device.get("schedules") or []
            for index, schedule in enumerate(schedules, 1):
                yield device, index, schedule


if __name__ == "__main__":
    pass
