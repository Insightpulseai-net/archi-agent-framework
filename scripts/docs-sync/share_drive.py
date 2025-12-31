#!/usr/bin/env python3
"""
Share Google Drive files/folders with a service account.
Uses your user OAuth credentials to grant access.

Usage:
    SA_EMAIL='svc@...' DRIVE_IDS='id1,id2,...' python share_drive.py
"""
import os
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    sa_email = os.environ.get("SA_EMAIL")
    ids = os.environ.get("DRIVE_IDS", "").strip()

    if not sa_email or not ids:
        print(
            "Usage: SA_EMAIL='svc@...' DRIVE_IDS='id1,id2,...' python share_drive.py",
            file=sys.stderr,
        )
        sys.exit(2)

    # OAuth flow - will open browser for user consent
    flow = InstalledAppFlow.from_client_secrets_file("client_oauth.json", SCOPES)
    creds = flow.run_local_server(port=0)

    drive = build("drive", "v3", credentials=creds)

    for file_id in [x.strip() for x in ids.split(",") if x.strip()]:
        perm = {
            "type": "user",
            "role": "reader",  # change to "writer" if needed
            "emailAddress": sa_email,
        }
        try:
            r = drive.permissions().create(
                fileId=file_id,
                body=perm,
                sendNotificationEmail=False,
                supportsAllDrives=True,
            ).execute()
            print(f"✅ Shared {file_id} -> {sa_email} (permId={r.get('id')})")
        except Exception as e:
            print(f"❌ Failed to share {file_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
