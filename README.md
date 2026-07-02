# NFC → Dropbox Spreadsheet Logger

Tap an NFC tag with your iPhone → a row gets added to a spreadsheet in your Dropbox.

```
  Tap NFC tag
      │
      ▼
  iPhone "Automations" (Shortcuts app)
      │   sends an HTTP POST with the tag name + your secret token
      ▼
  Your web service  (app.py, running on a free host)
      │   appends a row: timestamp + tag name
      ▼
  Spreadsheet in Dropbox  (/nfc_log.xlsx)
```

No Mac and no Xcode required. You'll set up three things:

1. **Dropbox** — so the app has somewhere to write.
2. **The web service** — deploy `app.py` to a free host (Render).
3. **Your iPhone** — a Shortcuts automation triggered by the NFC tag.

Give yourself ~30–45 minutes the first time. Follow the parts in order.

---

## Part 1 — Set up Dropbox (about 10 minutes)

**1.1 Create a Dropbox app**

1. Go to <https://www.dropbox.com/developers/apps> and click **Create app**.
2. Choose **Scoped access**.
3. Choose **App folder** (not "Full Dropbox"). This keeps the app limited to
   one folder — safer, and plenty for this.
4. Name it something like `nfc-logger` and click **Create app**.

**1.2 Give it permission to read/write files**

1. On your new app's page, open the **Permissions** tab.
2. Check these boxes: `files.content.write` and `files.content.read`.
3. Click **Submit** at the bottom. (Do this *before* the next step, or your
   token won't have the right permissions.)

**1.3 Copy your keys**

1. Go back to the **Settings** tab.
2. Copy the **App key** and **App secret** — you'll need them in a moment.

**1.4 Get a refresh token (one time)**

This gives your server permanent permission to write, without you logging in
again. On your own computer (Windows/Linux both fine):

```bash
pip install dropbox
python get_refresh_token.py
```

Follow the prompts: it prints a URL, you open it and click **Allow**, Dropbox
shows you a code, you paste the code back, and it prints your **refresh token**.
Copy that token somewhere safe for the next part.

> You now have three secrets: **App key**, **App secret**, **Refresh token**.

---

## Part 2 — Deploy the web service (about 10 minutes)

We'll use **Render** (free tier, gives you a public HTTPS web address). You'll
put this project on GitHub, then point Render at it.

**2.1 Put the code on GitHub**

1. Create a free account at <https://github.com> if you don't have one.
2. Create a new **empty** repository (e.g. `nfc-dropbox-logger`).
3. Upload all the files in this folder to it. Easiest no-command-line way:
   on the new repo page click **uploading an existing file**, then drag in
   every file from this project. Commit.

**2.2 Create the Render service**

1. Sign up at <https://render.com> (you can log in with GitHub).
2. Click **New +** → **Web Service** and connect the repo you just made.
3. Render should auto-detect the settings from `render.yaml`. If it asks:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
   - **Plan:** Free

**2.3 Add your secrets**

In the Render service's **Environment** section, add these variables:

| Key                     | Value                                                    |
| ----------------------- | -------------------------------------------------------- |
| `API_TOKEN`             | Make up a long random string (your password)             |
| `DROPBOX_APP_KEY`       | From Dropbox Settings                                    |
| `DROPBOX_APP_SECRET`    | From Dropbox Settings                                    |
| `DROPBOX_REFRESH_TOKEN` | The token from `get_refresh_token.py`                    |
| `DROPBOX_FILE_PATH`     | `/nfc_log.xlsx`                                          |
| `TIMEZONE`              | `America/Chicago` (Dallas time; change if you like)      |

Click **Create Web Service** / **Deploy**. After a minute or two Render gives
you a URL like `https://nfc-dropbox-logger.onrender.com`.

**2.4 Test it**

Open the URL in a browser. You should see:

```json
{"status": "ok", "service": "nfc-dropbox-logger"}
```

Now test a real log entry. Replace the URL and token below and run it in a
terminal (or use any REST client):

```bash
curl -X POST "https://YOUR-APP.onrender.com/log" \
  -H "Content-Type: application/json" \
  -d '{"tag": "test tag", "token": "YOUR_API_TOKEN"}'
```

You should get back `{"status": "logged", ...}` — and a new file
`nfc_log.xlsx` will appear in your Dropbox under
**Apps → nfc-logger** (or whatever you named the app). Open it and you'll see
your test row.

> **Heads up on the free tier:** Render's free services go to sleep after
> ~15 minutes idle, so the *first* tap after a while may take 30–60 seconds
> while it wakes up. Later taps are instant. That's usually fine for a class
> project. (If you want it always-on, that's a paid plan.)

---

## Part 3 — Set up your iPhone (about 10 minutes)

**3.1 Write your NFC tag's automation**

1. Open the **Shortcuts** app on your iPhone.
2. Tap the **Automation** tab at the bottom.
3. Tap **+** (top right) → **Create Personal Automation**.
4. Scroll down and tap **NFC**.
5. Tap **Scan**, then hold your NFC tag to the top of your phone. Give the
   tag a name when asked (e.g. `front door`). Tap **Next**.

**3.2 Add the "send to my app" action**

1. Tap **New Blank Automation** / **Add Action**.
2. Search for **Get Contents of URL** and add it.
3. Tap the **URL** field and enter your log endpoint:
   `https://YOUR-APP.onrender.com/log`
4. Tap **Show More** to expand the options, then set:
   - **Method:** `POST`
   - **Request Body:** `JSON`
   - Under the body, tap **Add new field** → **Text**, key `tag`,
     value `front door` (use this tag's name).
   - Tap **Add new field** → **Text**, key `token`,
     value = your `API_TOKEN` (the long random string).
5. Tap **Next**, then turn **OFF** "Ask Before Running" so it logs
   automatically on tap. Confirm **Don't Ask**. Tap **Done**.

**3.3 Try it**

Tap your phone to the NFC tag. Within a moment a new row should appear in your
`nfc_log.xlsx` in Dropbox. 🎉

For **more tags**, repeat Part 3 for each one — just change the `tag` value
(e.g. `gym`, `desk`, `car`) so you can tell them apart in the sheet.

---

## What a logged row looks like

| timestamp_utc         | timestamp_local       | tag        |
| --------------------- | --------------------- | ---------- |
| 2026-07-01 23:53:11   | 2026-07-01 18:53:11   | front door |
| 2026-07-01 23:59:02   | 2026-07-01 18:59:02   | gym        |

---

## Test it on your own computer first (optional)

Before deploying, you can confirm the code works locally — no Dropbox needed:

```bash
pip install -r requirements.txt
python test_local.py
```

It sends fake taps and writes `local_test_output.xlsx` so you can open it and
see the rows. (This uses a stand-in for Dropbox, so nothing touches your real
account.)

---

## Troubleshooting

- **Browser shows the health message but taps don't log** → double-check the
  URL ends in `/log`, the Method is `POST`, and the `token` value exactly
  matches `API_TOKEN`.
- **`unauthorized` error** → the `token` in Shortcuts doesn't match
  `API_TOKEN` in Render. They must be identical.
- **`missing 'tag'` error** → the JSON body field is named `tag` (lowercase).
- **First tap of the day is slow** → that's the free host waking up; normal.
- **No file in Dropbox** → confirm you clicked **Submit** on the Dropbox
  Permissions tab *before* generating the refresh token. If not, re-run
  `get_refresh_token.py` and update the token in Render.

---

## Files in this project

| File                    | What it is                                             |
| ----------------------- | ------------------------------------------------------ |
| `app.py`                | The web service. Receives taps, writes to Dropbox.     |
| `get_refresh_token.py`  | One-time helper to connect your Dropbox account.       |
| `test_local.py`         | Local smoke test (no Dropbox account needed).          |
| `requirements.txt`      | Python packages the app needs.                         |
| `Procfile`              | Tells the host how to start the app.                   |
| `render.yaml`           | One-click deploy settings for Render.                  |
| `.env.example`          | Template for your secret values (local testing).       |
| `.gitignore`            | Keeps your secrets out of GitHub.                      |

---

## A note for your class write-up

This project is a small **event-driven web service**: a physical NFC trigger
fires a mobile automation, which calls a REST API you wrote, which
authenticates the request and persists structured data to cloud storage. If
you later want to add the machine-learning angle, the spreadsheet becomes your
dataset — e.g. predict which tag you'll tap next based on time of day, or flag
unusual patterns. The logger is the data-collection layer that a model would
sit on top of.
#   N F C _ E v e n t _ L o g g e r  
 