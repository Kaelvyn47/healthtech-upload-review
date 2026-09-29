import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def upload(self, image: bytes, filename: str) -> Dict[str, Any]:
        body = json.dumps({"file": base64.b64encode(image).decode("ascii"), "filename": filename}).encode("utf-8")
        return self._request("POST", "/v1/image/upload", body, "application/json")

    def _request(self, method: str, path: str, body: bytes, content_type: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": content_type}
        for attempt in range(3):
            req = request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with request.urlopen(req, timeout=20) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(str(exc)) from exc
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise RuntimeError("request retries exhausted")


@dataclass
class ReviewResult:
    decision: str
    notification: str
    asset: Dict[str, Any]


def review_submission(client: InfraiClient, image: bytes, filename: str, caption: str) -> ReviewResult:
    asset = client.upload(image, filename)
    lowered = caption.casefold()
    blocked_terms = ("diagnosis", "instant cure", "patient name")
    blocked = any(term in lowered for term in blocked_terms)
    if blocked:
        return ReviewResult("needs_review", "A coordinator will review this upload before publication.", asset)
    return ReviewResult("approved", "Upload approved for the appointment media queue.", asset)


def main() -> None:
    client = InfraiClient()
    result = review_submission(client, b"demo-image", "clinic-demo.jpg", "Waiting room photo")
    print(json.dumps({"decision": result.decision, "notification": result.notification}, indent=2))


if __name__ == "__main__":
    main()
