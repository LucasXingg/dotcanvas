from typing import Any, Dict, Optional

import logging
import requests

logger = logging.getLogger("dot.api")

class APIClient:
    def __init__(self, key: str, base_url: str = "https://dot.mindreset.tech/api/open/image") -> None:
        self.base_url = base_url
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
        timeout: Optional[float] = 10.0,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "refreshNow": refresh_now,
            "deviceId": device_id,
            "image": image,
            "border": border,
            "ditherType": dither_type,
            "ditherKernel": dither_kernel,
        }

        if link:
            payload["link"] = link

        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            logger.error(f"api error ({response.status_code}): {response.json()}")

        logger.debug(f"Success ({response.status_code}): {response.json()}")
