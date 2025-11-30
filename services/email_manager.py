import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- UPDATED SCOPES: Added 'gmail.compose' ---
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.compose" 
]

class EmailManager:
    def __init__(self):
        self.creds = None
        self.service_gmail = None
        self.service_sheets = None
        self.authenticate()

    def authenticate(self):
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        self.service_gmail = build("gmail", "v1", credentials=self.creds)
        self.service_sheets = build("sheets", "v4", credentials=self.creds)

    def fetch_recent_emails(self, count=5):
        # (Keep your existing fetch code exactly as it was)
        results = self.service_gmail.users().messages().list(userId="me", maxResults=count).execute()
        messages = results.get("messages", [])
        email_data = []
        if not messages: return []
        
        for message in messages:
            msg = self.service_gmail.users().messages().get(userId="me", id=message["id"]).execute()
            payload = msg["payload"]
            headers = payload.get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            snippet = msg.get("snippet", "")
            email_data.append({"id": message["id"], "subject": subject, "sender": sender, "snippet": snippet})
        return email_data

    def log_to_sheet(self, data):
        # (Keep your existing sheet code)
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        values = [[data.customer_name, data.order_id, data.category, data.sentiment, data.summary]]
        body = {'values': values}
        try:
            self.service_sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range="Sheet1!A:E", valueInputOption="USER_ENTERED", body=body
            ).execute()
        except Exception as e:
            print(f"Sheet Error: {e}")

    # --- NEW FUNCTION: CREATE DRAFT ---
    def create_draft(self, to_email, subject, body_text):
        """Creates a draft email in Gmail."""
        try:
            message = EmailMessage()
            message.set_content(body_text)
            message["To"] = to_email
            message["Subject"] = subject

            # Encode the message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"message": {"raw": encoded_message}}

            draft = self.service_gmail.users().drafts().create(
                userId="me", body=create_message
            ).execute()
            
            print(f"✅ Draft created: {draft['id']}")
            return True
        except Exception as e:
            print(f"❌ Draft Error: {e}")
            return False