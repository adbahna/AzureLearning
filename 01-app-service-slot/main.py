"""
Small status web app for the Azure labs.

It exists to make platform behavior visible, not to do anything useful:
  - a version banner so you can watch a slot swap take effect (Lab 1)
  - the host name and slot so you can tell instances and VMs apart (Labs 1 and 7)
  - a slow endpoint and an error endpoint so there is something to see in
    Application Insights (Lab 3)

Environment variables it reads:
  APP_VERSION   shown in the banner (default "1.0.0"). In Lab 1, set this to a
                different value on the staging and production slots, then swap
                and watch the banner change.
"""

import os
import socket
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Azure Lab App")

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def host_name() -> str:
    return socket.gethostname()


def slot_name() -> str:
    # App Service sets WEBSITE_SLOT_NAME (e.g. "production" or "staging").
    # It is empty on the Lab 7 VMs, which is fine.
    return os.getenv("WEBSITE_SLOT_NAME", "")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    slot = slot_name()
    slot_row = f"<tr><td>Slot</td><td>{slot}</td></tr>" if slot else ""
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Azure Lab App</title>
<style>
  body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         margin: 0; background: #0f172a; color: #e2e8f0; }}
  .wrap {{ max-width: 640px; margin: 0 auto; padding: 48px 24px; }}
  .banner {{ background: #2563eb; color: white; border-radius: 12px;
            padding: 28px 24px; text-align: center; }}
  .banner .label {{ font-size: 13px; letter-spacing: 0.08em;
                   text-transform: uppercase; opacity: 0.85; }}
  .banner .version {{ font-size: 44px; font-weight: 700; margin-top: 6px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; }}
  td:first-child {{ color: #94a3b8; width: 120px; }}
  td:last-child {{ font-family: ui-monospace, monospace; }}
  .links {{ margin-top: 28px; }}
  .links a {{ display: inline-block; margin-right: 14px; color: #93c5fd;
             text-decoration: none; font-size: 14px; }}
  .hint {{ margin-top: 32px; color: #64748b; font-size: 13px; line-height: 1.6; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="banner">
      <div class="label">Running version</div>
      <div class="version">{APP_VERSION}</div>
    </div>
    <table>
      <tr><td>Host</td><td>{host_name()}</td></tr>
      {slot_row}
      <tr><td>Time</td><td>{now}</td></tr>
    </table>
    <div class="links">
      <a href="/api/info">/api/info</a>
      <a href="/api/slow">/api/slow</a>
      <a href="/api/error">/api/error</a>
      <a href="/health">/health</a>
    </div>
    <div class="hint">
      Change APP_VERSION and redeploy, or swap slots, and this banner changes.
      The slow and error endpoints give Application Insights something to capture.
    </div>
  </div>
</body>
</html>"""


@app.get("/health")
def health() -> JSONResponse:
    # Target this from an App Service health check or a load balancer probe.
    return JSONResponse({"status": "ok", "version": APP_VERSION})


@app.get("/api/info")
def info() -> JSONResponse:
    # Quick to curl. Use it to confirm which VM answered through the load
    # balancer in Lab 7, or which version a slot is serving in Lab 1.
    return JSONResponse({
        "version": APP_VERSION,
        "host": host_name(),
        "slot": slot_name(),
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@app.get("/api/slow")
def slow(seconds: float = 1.5) -> JSONResponse:
    # Adds latency so p95 has something to show in Application Insights.
    # Override with ?seconds=, capped at 10.
    seconds = max(0.0, min(seconds, 10.0))
    time.sleep(seconds)
    return JSONResponse({
        "version": APP_VERSION,
        "host": host_name(),
        "slept_seconds": seconds,
    })


@app.get("/api/error")
def error():
    # Unhandled on purpose so Application Insights records it as an exception
    # in the failures view, not just a clean 500.
    raise RuntimeError("Deliberate failure for the observability lab")
