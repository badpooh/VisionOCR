# -*- coding: utf-8 -*-
"""A3700N 제품용 DeviceIO — 브릿지(a3700n_bridge) 의 로컬 REST API 를 호출.

전제:
    a3700n_bridge 프로세스가 로컬에서 떠 있고 (기본 127.0.0.1:5580),
    이미 장치 텔넷 로그인 / 스크립트 배포가 끝나있다.

네트워크 호출은 브릿지 한 곳으로만 이루어지므로 여기선 장치 IP 를 몰라도 된다.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .io_base import DeviceIO, DeviceIOError


class A3700NDeviceIO(DeviceIO):
    product = "A3700N"

    def __init__(self, base_url: str = "http://127.0.0.1:5580", timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------
    def _get(self, path: str, raw: bool = False):
        url = f"{self.base_url}{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
        except urllib.error.URLError as e:
            raise DeviceIOError(f"GET {path} failed: {e}") from e
        if raw:
            return data
        return json.loads(data.decode("utf-8", "replace"))

    def _post(self, path: str, body: dict):
        url = f"{self.base_url}{path}"
        raw = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=raw, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
        except urllib.error.HTTPError as e:
            # 서버가 JSON 에러 바디를 줬을 수도
            try:
                msg = json.loads(e.read().decode("utf-8", "replace")).get("error", "")
            except Exception:
                msg = ""
            raise DeviceIOError(f"POST {path} {e.code}: {msg or e}") from e
        except urllib.error.URLError as e:
            raise DeviceIOError(f"POST {path} failed: {e}") from e
        return json.loads(data.decode("utf-8", "replace"))

    # ------------------------------------------------------------
    def touch(self, x: int, y: int) -> None:
        res = self._post("/touch", {"x": int(x), "y": int(y)})
        if not res.get("ok"):
            raise DeviceIOError(f"touch failed: {res}")

    def screenshot(self) -> bytes:
        return self._get("/screenshot", raw=True)

    def ping(self) -> bool:
        try:
            res = self._get("/status")
            return bool(res.get("connected"))
        except DeviceIOError:
            return False
