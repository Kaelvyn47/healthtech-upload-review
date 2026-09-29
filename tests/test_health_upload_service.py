import base64
import json

from src.health_upload_service import InfraiClient, ReviewResult, review_submission


class FakeClient:
    def upload(self, image, filename):
        return {"id": "asset-123", "filename": filename}


def test_caption_with_patient_name_waits_for_review():
    result = review_submission(FakeClient(), b"pixels", "visit.jpg", "Patient name visible")
    assert isinstance(result, ReviewResult)
    assert result.decision == "needs_review"
    assert "coordinator" in result.notification


def test_neutral_caption_enters_media_queue():
    result = review_submission(FakeClient(), b"pixels", "room.jpg", "Clinic waiting room")
    assert result.decision == "approved"


def test_upload_sends_json_file_and_filename(monkeypatch):
    client = InfraiClient(api_key="test")
    captured = {}

    def fake_request(method, path, body, content_type):
        captured.update(method=method, path=path, body=json.loads(body), content_type=content_type)
        return {"id": "asset-123"}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.upload(b"pixels", "room.jpg") == {"id": "asset-123"}
    assert captured == {
        "method": "POST",
        "path": "/v1/image/upload",
        "body": {"file": base64.b64encode(b"pixels").decode("ascii"), "filename": "room.jpg"},
        "content_type": "application/json",
    }
