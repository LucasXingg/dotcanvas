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
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            logger.error(f"api error ({response.status_code}): empty response")
            return None

        data = response.json()
        logger.debug(f"Success ({response.status_code}): {data}")
        return data
