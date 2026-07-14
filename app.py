""" Tiny web service to log event to csv on the user's Dropbox.
 HTTP POST to /log  ->  this app  -> appends a row to Dropbox csv
"""

import io
import os
from datetime import datetime, timezone
# __ Configuration (read once at startup) ____________________________________
HEADERS = ["timestamp_local", "s", "e"]
DEFAULT_SOURCE = "NFC"                                                # If a request doesn't say where it came from, assume it was an NFC tap

API_TOKEN = os.environ.get("API_TOKEN", "")                           # A secret you make up. Shortcuts must send it so strangers can't write to your sheet.
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY", "")               # From the Dropbox App Console.
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "")         # From the Dropbox App Console.
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN", "")   # Produced once by running get_refresh_token.py.
DROPBOX_FILE_PATH = os.environ.get("DROPBOX_FILE_PATH", "/log.csv")   # Where to store the CSV in Dropbox
TIMEZONE = os.environ.get("TIMEZONE", "America/Chicago")              # IANA tz name for the local column. If not set, assume CST/CDT.


try:
    # Python 3.9+ standard library
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

import dropbox
from dropbox.files import WriteMode
from flask import Flask, jsonify, request
import csv

app = Flask(__name__)


# __ Dropbox helpers ____________________________________
def get_dropbox_client():
    """Return an authenticated Dropbox client.
    Automatically trades the refresh token for a fresh short-lived access token as needed.
    """
    missing = [
        name
        for name, value in {
            "DROPBOX_APP_KEY": DROPBOX_APP_KEY,
            "DROPBOX_APP_SECRET": DROPBOX_APP_SECRET,
            "DROPBOX_REFRESH_TOKEN": DROPBOX_REFRESH_TOKEN,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError("Missing Dropbox config: " + ", ".join(missing) + ". Set these environment variables (see README).")

    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
    )


def download_rows(dbx):
    """Get the CSV as a list of rows. If the file doesn't exist yet, start with just the header."""
    try:
        _metadata, response = dbx.files_download(DROPBOX_FILE_PATH)
        text = response.content.decode("utf-8")          # bytes -> text
        return list(csv.reader(io.StringIO(text)))       # text  -> list of rows
    except dropbox.exceptions.ApiError as err:
        if err.error.is_path() and err.error.get_path().is_not_found():
            return [HEADERS]                             # brand-new file = header only
        raise


def upload_rows(dbx, rows):
    """Turn the list of rows back into CSV text and upload it, replacing the old file."""
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)                   # list of rows -> text
    dbx.files_upload(
        buffer.getvalue().encode("utf-8"),               # text -> bytes
        DROPBOX_FILE_PATH,
        mode=WriteMode.overwrite,
    )


def append_row(event, source, when_utc):
    """Append one row to the Dropbox CSV.
    """
    dbx = get_dropbox_client()
    rows = download_rows(dbx)

    # Keep the header row correct (also upgrades an older/short header).
    if rows and rows[0] and rows[0][0] == "timestamp_local":
        rows[0] = HEADERS
    else:
        rows.insert(0, HEADERS)

    # Build the local-time string.
    timestamp_local = when_utc.astimezone(ZoneInfo(TIMEZONE))

    # Column order must match HEADERS: timestamp_local, source, event
    rows.append([
        timestamp_local.strftime("%Y-%m-%d %H:%M:%S"),
        source,
        event
    ])
    rows[1:] = sorted(rows[1:], key=lambda row: row[0], reverse=True)
    upload_rows(dbx, rows)


# __ Routes ____________________________________
@app.get("/")
def health():
    """Simple health check so you can confirm the service is running."""
    return jsonify({"status": "ok", "service": "nfc-dropbox-logger"})

@app.route("/log", methods=["GET", "POST"])
def log_event():
    """Receive an event and append a row to Dropbox.
    Accepts GET (handy for testing by pasting a URL in a browser) or POST.
    Values come from JSON body, form fields, OR the query string (?event=...):
        token  (required)  must equal API_TOKEN
        source (required)  NFC, Voice, Text, Email, etc.
        event  (required)  "a blob I parse later"
    The token may also be sent as a query string (?token=...) or an
    "Authorization: Bearer <token>" header, whichever is easiest.
    """
    # Pull values from JSON, form, or query string — whichever is present.
    data = request.get_json(silent=True) or {}

    def field(name):
        return (
            data.get(name)
            or request.form.get(name)
            or request.args.get(name)
        )

    # Token can arrive several ways; accept the most convenient.
    token = field("k")
    auth_header = request.headers.get("Authorization", "")
    if not token and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()

    if not API_TOKEN:
        return jsonify({"error": "server missing API_TOKEN config"}), 500
    if token != API_TOKEN:
        return jsonify({"error": "unauthorized"}), 401

    event = field("e")
    if not event:
        return jsonify({"error": "missing 'event'"}), 400
    
    # Where did this come from? NFC, Voice, Text, Email, etc.
    # source = field("s") or DEFAULT_SOURCE # If the sender didn't say, assume NFC.
    source = field("s")
    if not source:
        return jsonify({"error": "missing 'source'"}), 400

    when_utc = datetime.now(timezone.utc)

    try:
        append_row(str(event), str(source), when_utc)
    except Exception as exc:  # noqa: BLE001 - report any failure to the caller
        return jsonify({"error": str(exc)}), 500

    return jsonify({
        "status": "logged",
        "event": event,
        "source": source,
        "timestamp_utc": when_utc.strftime("%Y-%m-%d %H:%M:%S"),
    })

if __name__ == "__main__":
    # Local development server. In production, gunicorn runs the app (see Procfile).
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)

