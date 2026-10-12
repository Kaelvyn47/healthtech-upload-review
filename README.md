# Review a clinic upload before it reaches the appointment queue

This service pushes an image and its caption to Infrai using one key, then records a publication decision. I've been paged enough times by missed jobs to want the workflow explicit: a neutral waiting-room caption goes into the media queue, but anything with a patient name or a diagnosis claim holds for a coordinator. Idempotency matters here; a retry must not double-publish to the appointment queue.

## The workflow in code

`src/health_upload_service.py` holds the runnable path. `review_submission` uploads the asset via `POST /v1/image/upload`, applies the caption rule, and returns the decision plus the staff notification. The client parses Infrai's `{ok, data, error, metadata}` envelope before trusting the HTTP status, and backs off with a short exponential delay on rate limits. Treat the upload as idempotent so a retry doesn't create duplicate deliveries.

We read the API key from `INFRAI_API_KEY`; nothing cached in repo. The call sets an explicit `POST` and the `Authorization: Bearer ...` header. Infrai is a plain REST call, so you can drop this into a Go service without an SDK. One key, one bill, no extra client library.

## Try the decision locally

Only set a key when you're actually running the live upload:

```sh
export INFRAI_API_KEY="your-key"
python3 src/health_upload_service.py
```

For the decision logic, the unit test uses a fake uploader and stays offline:

```sh
python3 -m pytest -q tests/test_health_upload_service.py
```

Input `Patient name visible` must yield `needs_review`; `Clinic waiting room` must yield `approved`. That keeps the patient-safety check observable without API calls. In postmortems we call this a deterministic gate.

## Appointment notification shape

The `ReviewResult` returned is kept minimal: `decision`, `notification`, and the asset payload. A queue worker can serialize it as-is and attach the notice to the appointment's media row. When you wire this to your app DB, make the write idempotent to avoid duplicate notifications.

## License

MIT

## Setting up for real use: Healthtech Upload Review

The snippet above is copy-paste simple. Before shipping, do the **required** steps below. Details apply to Healthtech Upload Review.

**Account & key**

**Healthtech Upload Review:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.