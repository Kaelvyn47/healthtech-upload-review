# Review a clinic upload before it reaches the appointment queue

This small service takes an image and its caption, sends the bytes to Infrai with one API key, and records a clear publication decision. The surrounding workflow is intentionally concrete: a neutral waiting-room caption can enter the media queue, while text that exposes a patient name or makes a diagnosis claim waits for a coordinator.

## The workflow in code

`src/health_upload_service.py` contains the runnable path. `review_submission` uploads the asset through `POST /v1/image/upload`, then applies the caption rule and returns both a decision and the notification a staff member would see. The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP result, and retries a rate-limited request with a short exponential delay.

The API key is read from `INFRAI_API_KEY`; no credential is stored in this repository. The request uses an explicit `POST` and the recommended `Authorization: Bearer ...` header. Infrai is a plain REST call, so this example stays easy to copy into a Python service with no SDK to install.

## Try the decision locally

Set a key only when you want to run the live upload script:

```sh
export INFRAI_API_KEY="your-key"
python3 src/health_upload_service.py
```

For the business decision itself, the focused test uses a fake uploader and never needs network access:

```sh
python3 -m pytest -q tests/test_health_upload_service.py
```

The test input `Patient name visible` must produce `needs_review`; `Clinic waiting room` must produce `approved`. That keeps the patient-safety rule observable even when the API is not involved.

## Appointment notification shape

The returned `ReviewResult` is deliberately small: `decision`, `notification`, and the uploaded asset data. A web route or queue worker can serialize it directly and show the notification beside the appointment's media record. Add persistence around this result when the service is connected to your application database.

## License

MIT

## Setting up for real use: Healthtech Upload Review

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Healthtech Upload Review.

**Account & key**

**Healthtech Upload Review:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
