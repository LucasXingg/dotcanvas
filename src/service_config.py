from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import yaml

logger = logging.getLogger("dot.config")

_CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"
DEFAULT_CONFIG_PATH = _CONFIGS_DIR / "config.yaml"

# Used when a Docker volume mounts an empty host `configs/` directory over
# `/app/configs`, hiding the image's baked-in config.yaml / config-example.yaml.
DEFAULT_CONFIG_TEMPLATE = """# 复制此文件为 config.yaml

api_key: "你的API密钥"
devices:
- name: 设备1
  device_id: "你的设备ID"
  schedules:
  # 任务示例
  - name: 新年倒计时
    canvas_id: countdown_canvas
    cron: '0 0 * * *' # 每天午夜更新
    params: {}
"""


def ensure_config_file(path: str | Path | None = None) -> Path:
    """Ensure ``configs/config.yaml`` exists and is writable.

    Empty volume mounts overlay the image's default configs directory. Create
    ``config.yaml`` (and ``config-example.yaml`` when missing) so the daemon
    and config UI can start without a manual ``cp`` on the host.
    """

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    example_path = config_dir / "config-example.yaml"
    if not example_path.exists():
        example_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
        logger.info("Created missing config example at %s", example_path)

    if not config_path.exists():
        # Prefer the on-disk example (may have been customized) over the
        # embedded template when seeding a fresh config.yaml.
        seed = example_path.read_text(encoding="utf-8")
        config_path.write_text(seed, encoding="utf-8")
        logger.info("Created missing config file at %s", config_path)

    return config_path


class ServercConfig:

    DEFAULT_PATH = DEFAULT_CONFIG_PATH

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = ensure_config_file(path)
        self.cfg: Dict[str, Any] = {}
        self.load_config()


    def load_config(self) -> None:
        if not self.path.exists():
            msg = f"Config file not found: {self.path}"
            raise FileNotFoundError(msg)
        with self.path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            msg = "Configuration root must be a mapping"
            raise ValueError(msg)
        self.cfg = self._normalise_config(data)


    def _normalise_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = deepcopy(data)

        disabled = payload.get("disabled", False)
        if isinstance(disabled, bool):
            payload["disabled"] = disabled
        elif isinstance(disabled, str):
            payload["disabled"] = disabled.strip().lower() in {"true", "1", "yes", "on"}
        else:
            payload["disabled"] = bool(disabled)

        api_key = payload.get("api_key", "")
        payload["api_key"] = api_key if isinstance(api_key, str) else str(api_key)

        devices = payload.get("devices")
        normalised_devices: list[dict[str, Any]] = []
        if isinstance(devices, list):
            for device in devices:
                if not isinstance(device, dict):
                    continue
                device_copy = deepcopy(device)
                name = device_copy.get("name", "")
                if not isinstance(name, str):
                    name = str(name)
                device_copy["name"] = name

                device_id = device_copy.get("device_id", "")
                if not isinstance(device_id, str):
                    device_id = str(device_id)
                device_copy["device_id"] = device_id

                schedules = device_copy.get("schedules")
                normalised_schedules: list[dict[str, Any]] = []
                if isinstance(schedules, list):
                    for schedule in schedules:
                        if not isinstance(schedule, dict):
                            continue
                        schedule_copy = deepcopy(schedule)
                        for field in ("name", "canvas_id", "cron"):
                            value = schedule_copy.get(field, "")
                            if not isinstance(value, str):
                                schedule_copy[field] = str(value)
                        params = schedule_copy.get("params")
                        if not isinstance(params, dict):
                            schedule_copy["params"] = {}
                        disabled = schedule_copy.get("disabled", False)
                        if isinstance(disabled, bool):
                            schedule_copy["disabled"] = disabled
                        elif isinstance(disabled, str):
                            schedule_copy["disabled"] = disabled.strip().lower() in {"true", "1", "yes", "on"}
                        else:
                            schedule_copy["disabled"] = bool(disabled)
                        normalised_schedules.append(schedule_copy)
                device_copy["schedules"] = normalised_schedules
                normalised_devices.append(device_copy)

        payload["devices"] = normalised_devices
        return payload

    def validate(self, *, verbose: bool = True) -> bool:
        errors = self.collect_errors(self.cfg)

        if errors:
            if verbose:
                print("Validation FAILED:")
                for error in errors:
                    print(f" - {error}")
            return False
        if verbose:
            print("Validation OK: no obvious errors found")
        return True

    def collect_errors(self, data: Dict[str, Any]) -> list[str]:
        errors: list[str] = []

        api_key = data.get("api_key")
        if not api_key or not isinstance(api_key, str):
            errors.append("api_key is missing")

        devices = data.get("devices")
        if not devices:
            errors.append("devices is missing or empty")
        elif not isinstance(devices, list):
            errors.append("devices must be a list")
        else:
            for idx, device in enumerate(devices, 1):
                if not isinstance(device, dict):
                    errors.append(f"device[{idx}] must be a mapping")
                    continue
                name = device.get("name")
                device_id = device.get("device_id")
                if not name:
                    errors.append(f"device[{idx}].name is missing")
                if not device_id:
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
                    if not schedule.get("name"):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].name is missing"
                        )
                    if not schedule.get("canvas_id"):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].canvas_id is missing"
                        )
                    params = schedule.get("params")
                    if params is None:
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].params is missing"
                        )
                    elif not isinstance(params, dict):
                        errors.append(
                            f"device[{idx}].schedules[{sidx}].params must be a mapping"
                        )

        return errors


    def iter_device_schedules(self) -> Iterator[Tuple[Dict[str, Any], int, Dict[str, Any]]]:
        devices = self.cfg.get("devices") or []
        for device in devices:
            schedules = device.get("schedules") or []
            for index, schedule in enumerate(schedules, 1):
                yield device, index, schedule

    def get_api_key(self) -> str:
        return self.cfg.get("api_key", "")

    def as_dict(self) -> Dict[str, Any]:
        return deepcopy(self.cfg)

    def update_and_save(self, data: Dict[str, Any]) -> list[str]:
        normalised = self._normalise_config(data)
        errors = self.collect_errors(normalised)
        if errors:
            return errors
        self.cfg = normalised
        self.save_config()
        return []

    def save_config(self) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.cfg, fh, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    pass
