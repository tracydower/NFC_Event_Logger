"""
One-time helper: get a Dropbox REFRESH TOKEN.
=============================================

You run this ONCE on your own computer. It gives you a refresh token that
you paste into your app's environment variables. After that the server can
write to Dropbox forever without you logging in again.

Before running, you need your app key and secret from the Dropbox App
Console (https://www.dropbox.com/developers/apps). See the README.

Usage:
    pip install dropbox
    python get_refresh_token.py

Then follow the on-screen instructions: it opens a URL, you approve access,
Dropbox shows you a code, you paste the code back here, and it prints your
refresh token.
"""

import dropbox

print("=" * 60)
print(" Dropbox refresh-token helper")
print("=" * 60)
print()

app_key = input("Paste your Dropbox APP KEY: ").strip()
app_secret = input("Paste your Dropbox APP SECRET: ").strip()

if not app_key or not app_secret:
    raise SystemExit("App key and secret are both required. Exiting.")

# token_access_type="offline" is what makes Dropbox hand back a refresh token.
auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
    app_key,
    consumer_secret=app_secret,
    token_access_type="offline",
)

authorize_url = auth_flow.start()

print()
print("1. Open this URL in your browser:")
print()
print("   " + authorize_url)
print()
print("2. Click 'Allow' (you may have to log in first).")
print("3. Copy the authorization code Dropbox shows you.")
print()

auth_code = input("4. Paste the authorization code here: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"\nFailed to finish auth: {exc}")

print()
print("=" * 60)
print(" SUCCESS! Here is your refresh token:")
print("=" * 60)
print()
print(oauth_result.refresh_token)
print()
print("Copy the line above and set it as DROPBOX_REFRESH_TOKEN")
print("(in your .env file locally, and in Render's Environment settings).")
print("Keep it secret — it grants access to your app's Dropbox folder.")
