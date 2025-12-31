#!/usr/bin/env python3
"""
Verify that a service account can access Google Drive files.

Usage:
    GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json" DRIVE_IDS="id1,id2" python verify_sa_access.py
"""
import os
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account


def main():
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    ids = os.environ.get("DRIVE_IDS", "").strip()

    if not key_path or not ids:
        print(
            "Usage: GOOGLE_APPLICATION_CREDENTIALS='path' DRIVE_IDS='id1,id2' python verify_sa_access.py",
            file=sys.stderr,
        )
        sys.exit(2)

    creds = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive = build("drive", "v3", credentials=creds)

    ok = True
    for file_id in [x.strip() for x in ids.split(",") if x.strip()]:
        try:
            meta = drive.files().get(fileId=file_id, fields="id,name,mimeType").execute()
            print(f"✅ OK {meta['id']} {meta['mimeType']} {meta['name']}")
        except Exception as e:
            ok = False
            print(f"❌ FAIL {file_id} {str(e)}", file=sys.stderr)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
