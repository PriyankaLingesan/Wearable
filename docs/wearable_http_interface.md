# Wearable HTTP interface

The wrist unit and the companion exchange **one HTTP request and response**. There is no broker, no topics, no retained state and no device registry.

```
python -m acquisition.server --host 0.0.0.0      # companion, default port 5060
```

## Request
`POST /api/wearable/upload` with the JPEG bytes as the body and `Content-Type: image/jpeg`. Optional query `?risk=0.05` (accepted-error target, default 0.05).

## Reply (text/plain)
| HTTP | Body |
|---|---|
| 200 | three lines: `READ OK` / `RETAKE` / `NO MARK`; the transcription (READ OK) or the recapture hint; the readability label |
| 400, 422 | `BAD IMAGE`, then the reason (empty, not an image, truncated, blank, too small) |
| 500 | `ERROR`, then the exception name; no result is invented |

The companion stores the bytes unchanged (`captures/wrn-<time>-<id>.jpg`, SHA-256 in the metadata, source "wearable"), validates them, and calls the same `process_stored()` as the webcam and upload paths, so identical pixels give identical results.

## Browser
`GET /api/wearable/latest` returns the last wearable result (JSON, includes a counter `seq`); the "Wearable camera" tab (labelled PROPOSED, UNTESTED) polls it every 2 s.

## Status
* Tested with a Python client (`tests/test_wearable_http.py`, 4 tests).
* Not tested: the device, the camera, a real Wi-Fi link. Plain HTTP on a local network; no authentication or TLS.
