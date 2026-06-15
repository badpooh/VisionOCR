# -*- coding: utf-8 -*-
"""A2700 DeviceIO using UT_Bridge REST endpoints."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .io_base import DeviceIO, DeviceIOError


class A2700DeviceIO(DeviceIO):
    product = "A2700"

    def __init__(self, base_url: str | None = None, timeout: float = 60.0):
        self.base_url = (
            base_url
            or os.environ.get("VISIONOCR_A2700_BRIDGE_URL")
            or "http://127.0.0.1:5580"
        ).rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, raw: bool = False):
        url = f"{self.base_url}{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type", "")
        except urllib.error.URLError as e:
            raise DeviceIOError(f"GET {path} failed: {e}") from e

        if raw:
            return data
        if "application/json" in content_type:
            return json.loads(data.decode("utf-8", "replace"))
        return {"ok": True, "content_type": content_type, "bytes": len(data)}

    def _post(self, path: str, body: dict):
        url = f"{self.base_url}{path}"
        raw = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=raw,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8", "replace")).get("error", "")
            except Exception:
                msg = ""
            raise DeviceIOError(f"POST {path} {e.code}: {msg or e}") from e
        except urllib.error.URLError as e:
            raise DeviceIOError(f"POST {path} failed: {e}") from e

        if "application/json" in content_type:
            return json.loads(data.decode("utf-8", "replace"))

        if "image/png" in content_type or data.startswith(b"\x89PNG\r\n\x1a\n"):
            return {
                "ok": True,
                "content_type": content_type or "image/png",
                "bytes": len(data),
            }

        return {"ok": True, "content_type": content_type, "bytes": len(data)}

    def touch(self, x: int, y: int) -> None:
        res = self._post("/touch", {"x": int(x), "y": int(y)})
        if not res.get("ok", True):
            raise DeviceIOError(f"touch failed: {res}")

    def button(self, keyin: int) -> None:
        res = self._post("/button", {"keyin": int(keyin)})
        if not res.get("ok", True):
            raise DeviceIOError(f"button failed: {res}")

    def screenshot(self) -> bytes:
        png = self._get("/screenshot", raw=True)
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise DeviceIOError(f"screenshot is not PNG: head={png[:16].hex()}")
        return png

    def ping(self) -> bool:
        try:
            res = self._get("/status")
            return bool(res.get("ok") or res.get("connected"))
        except DeviceIOError:
            return False
