# ingestion/gmail_connector.py
"""
Google Gmail API OAuth2 Ingestion Connector.
Fetches real emails using the official Google API Client Library.
"""

import base64
from pathlib import Path
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.models import RawEmail
from core.config import settings
from core.logger import get_logger
from ingestion.base import EmailIngestionProvider

logger = get_logger("gmail_connector")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailConnector(EmailIngestionProvider):
    def __init__(self, credentials_path: str = None, token_path: str = None):
        self.credentials_path = Path(credentials_path or settings.gmail_credentials_path)
        self.token_path = Path(token_path or settings.gmail_token_path)
        self.service = None

    def authenticate(self) -> bool:
        """Authenticates with Gmail API via OAuth2 token or flow."""
        creds = None
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                logger.warning(f"Could not load existing token: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                if not self.credentials_path.exists():
                    logger.warning(
                        f"Gmail credentials not found at {self.credentials_path}. "
                        f"Use MockEmailGenerator or provide credentials.json to connect live Gmail."
                    )
                    return False
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(self.token_path, "w", encoding="utf-8") as token_file:
                        token_file.write(creds.to_json())
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return False

        try:
            self.service = build("gmail", "v1", credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return False

    def fetch_emails(self, max_count: int = 25) -> List[RawEmail]:
        """Fetches latest unread/inbox emails from Gmail."""
        if not self.service:
            if not self.authenticate():
                return []

        try:
            results = self.service.users().messages().list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_count
            ).execute()

            messages = results.get("messages", [])
            raw_emails = []

            for msg in messages:
                detail = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="full"
                ).execute()

                payload = detail.get("payload", {})
                headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

                subject = headers.get("subject", "No Subject")
                sender = headers.get("from", "Unknown Sender")
                timestamp = headers.get("date", "")
                body = self._extract_body(payload)

                raw_emails.append(RawEmail(
                    id=msg["id"],
                    subject=subject,
                    sender=sender,
                    body=body,
                    timestamp=timestamp
                ))

            return raw_emails
        except Exception as e:
            logger.error(f"Error fetching emails from Gmail: {e}")
            return []

    def _extract_body(self, payload: dict) -> str:
        """Recursively parses MIME parts to retrieve plain text or HTML body."""
        if not payload:
            return ""

        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")
                except Exception:
                    pass

        # Check sub-parts
        for part in payload.get("parts", []):
            extracted = self._extract_body(part)
            if extracted:
                return extracted

        # Fallback to top-level body data
        data = payload.get("body", {}).get("data", "")
        if data:
            try:
                return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")
            except Exception:
                pass

        return ""
