"""
Try app.py on your own computer — no Dropbox, no secrets, no risk.
Runs app.py but swaps Dropbox for a plain file on your PC, so you can see exactly what rows your code produces.
How to run (Windows):
    1. Save this file next to app.py  
    2. Open a terminal there and run:   pip install flask
    3. Run:   python try_it_locally.py
    4. It creates  log.csv  in the same folder — open it and look.
"""
LOCAL_FILE = "log.csv"

import csv
import os
import time

# Dummy values so app.py imports cleanly. Real Dropbox is never contacted.
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("DROPBOX_APP_KEY", "x")
os.environ.setdefault("DROPBOX_APP_SECRET", "x")
os.environ.setdefault("DROPBOX_REFRESH_TOKEN", "x")

import app as service  # your real app.py

if not os.path.exists(LOCAL_FILE):
    with open(LOCAL_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(service.HEADERS)

# A stand-in for Dropbox that just reads/writes the local file above.
class FakeDropbox:
    def files_download(self, path):
        with open(LOCAL_FILE, "rb") as f:
            data = f.read()
        return (None, type("R", (), {"content": data})())

    def files_upload(self, data, path, mode=None):
        with open(LOCAL_FILE, "wb") as f:
            f.write(data)

# Make your app use the fake Dropbox instead of the real one.
service.get_dropbox_client = lambda: FakeDropbox()

client = service.app.test_client()

# --- Send some pretend taps -------------------------------------------------
print("Sending test logs...\n")
print(client.post("/log", json={"k": "test-token", "s": "NFC|TEST:aaaaaaaaa",}).get_json())
time.sleep(30)
print(client.post("/log", json={"k": "test-token", "s": "Voice|TEST:bbbbbbbbbbb",}).get_json())
time.sleep(60)
print(client.post("/log", json={"k": "test-token", "s": "Text|TEST:ccccc",}).get_json())
time.sleep(120)
print(client.post("/log", json={"k": "test-token", "s": "App_Opened|TEST:dddddddddddddddddddddddddddddddddddd",}).get_json())

# --- Show the resulting file ------------------------------------------------
print(LOCAL_FILE)
with open(LOCAL_FILE, "r", encoding="utf-8") as f:
    print(f.read())

print(f"Done. Open '",LOCAL_FILE,"' in this folder to see it as a spreadsheet.")

