import sys

import yaml

class ServercConfig():

    PATH = "configs/config.yaml"

    def __init__(self):
        self.config: dict = {}
        self.load_config()


    def load_config(self) -> None:
        if not self.PATH.exists():
            print(f"Config file not found: {self.PATH}")
            sys.exit(2)
        with self.PATH.open("r", encoding="utf-8") as fh:
            self.cfg = yaml.safe_load(fh)


    def validate(self) -> bool:
        errors = []

        if not self.cfg.get("api_key"):
            errors.append("api_key is missing")

        devices = self.cfg.get("devices")
        if not devices:
            errors.append("devices is missing or empty")
        else:
            for idx, d in enumerate(devices, 1):
                if not d.get("name"):
                    errors.append(f"device[{idx}].name is missing")
                if not d.get("device_id"):
                    errors.append(f"device[{idx}].device_id is missing")
                schedules = d.get("schedules")
                if schedules is not None:
                    if not isinstance(schedules, list):
                        errors.append(f"device[{idx}].schedules must be a list")
                    else:
                        for sidx, s in enumerate(schedules, 1):
                            if not s.get("cron"):
                                errors.append(f"device[{idx}].schedules[{sidx}].cron is missing")
                            if not s.get("type"):
                                errors.append(f"device[{idx}].schedules[{sidx}].type is missing")
                            params = s.get("params")
                            if params is None:
                                errors.append(f"device[{idx}].schedules[{sidx}].params is missing")

        if errors:
            print("Validation FAILED:\n")
            for e in errors:
                print(" - ", e)
            return False
        else:
            print("Validation OK: no obvious errors found")
            return True


if __name__ == "__main__":
    pass
