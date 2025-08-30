# your_app/utils/google_drive.py
import io
import uuid
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Make sure these env vars exist in your Render settings:
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_DRIVE_FOLDER_ID
# and optionally: GOOGLE_SCOPES (list) but below we set default scope.

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    """
    Build a google drive service using client_id/secret and refresh_token from env.
    This uses an in-memory Credentials object and refreshes automatically when needed.
    """
    creds = Credentials(
        token=None,
        refresh_token=getattr(settings, "GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=getattr(settings, "GOOGLE_CLIENT_ID"),
        client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET"),
        scopes=getattr(settings, "GOOGLE_SCOPES", DEFAULT_SCOPES),
    )

    if not creds.valid or creds.expired:
        creds.refresh(Request())

    return build("drive", "v3", credentials=creds)


def upload_file_to_drive(file_obj, ext=None):
    """
    Upload file to Google Drive.
    ext is auto-detected if not provided.
    Supports: jpg, jpeg, png, webp
    """
    service = get_drive_service()
    generated_uuid = str(uuid.uuid4())

    # detect extension if not passed
    if not ext:
        filename = file_obj.name.lower()
        if filename.endswith(".jpeg"):
            ext = "jpeg"
        elif filename.endswith(".png"):
            ext = "png"
        elif filename.endswith(".webp"):
            ext = "webp"
        else:
            ext = "jpg"  # fallback

    filename = f"{generated_uuid}.{ext}"

    metadata = {
        "name": filename,
        "parents": [getattr(settings, "GOOGLE_DRIVE_FOLDER_ID")],
    }

    file_bytes = io.BytesIO(file_obj.read())

    try:
        # webp needs correct mimetype: image/webp
        media = MediaIoBaseUpload(file_bytes, mimetype=f"image/{ext}", resumable=False)
        uploaded = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()

        service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
        ).execute()

        return uploaded["id"], generated_uuid

    finally:
        file_bytes.close()


def get_public_url(google_file_id):
    return f"https://drive.google.com/uc?id={google_file_id}"