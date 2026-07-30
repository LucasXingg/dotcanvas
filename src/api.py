from typing import Any, Dict, Optional
from urllib.parse import quote

import logging
import requests

logger = logging.getLogger("dot.api")

class APIClient:
    def __init__(
        self,
        key: str,
        base_url: str = "https://dot.mindreset.tech/api/authV2/open/device",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.key = key

    def send_image(
        self,
        *,
        device_id: str,
        image: str,
        refresh_now: bool = True,
        link: Optional[str] = None,
        border: int = 0,
        dither_type: str = "DIFFUSION",
        dither_kernel: str = "FLOYD_STEINBERG",
        task_key: Optional[str] = None,
        task_alias: Optional[str | int] = None,
        timeout: Optional[float] = 10.0,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "refreshNow": refresh_now,
            "image": image,
            "border": border,
            "ditherType": dither_type,
            "ditherKernel": dither_kernel,
        }

        if link:
            payload["link"] = link
        if task_key is not None:
            payload["taskKey"] = task_key
        if task_alias is not None:
            payload["taskAlias"] = task_alias

        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/{quote(device_id, safe='')}/image"
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            detail = ""
            if getattr(exc, "response", None) is not None:
                detail = (exc.response.text or "").strip()
            if status is not None:
                logger.error("api error (%s): %s", status, detail or exc)
            else:
                logger.error("api error: %s", exc)
            return None

        # 204 / empty body is a successful no-content response — not an error
        if response.status_code == 204 or not response.content:
            logger.debug("Success (%s): empty response", response.status_code)
            return None

        try:
            data = response.json()
        except ValueError:
            logger.error("api error (%s): invalid JSON response", response.status_code)
            return None

        logger.debug("Success (%s): %s", response.status_code, data)
        return data
