import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
# We ask for Read-Only Gmail access and Write access to Sheets.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]

class EmailManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Handles the OAuth 2.0 Login Flow."""
        # Check if we already have a valid login token
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If no valid credentials, let's log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # This requires your credentials.json file to be in the root folder
                if not os.path.exists("credentials.json"):
                    raise FileNotFoundError("credentials.json not found! Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        # 1. Build Gmail Service
        self.service_gmail = build("gmail", "v1", credentials=self.creds)
        
        # 2. Build Sheets Service (Make sure this is assigned to self.service_sheets)
        self.service_sheets = build("sheets", "v4", credentials=self.creds)

    def fetch_recent_emails(self, count=5):
        """Fetches the latest N emails to test the connection."""
        print(f"Fetching last {count} emails...")
        results = self.service_gmail.users().messages().list(userId="me", maxResults=count).execute()
        messages = results.get("messages", [])

        email_data = []

        if not messages:
            print("No messages found.")
        else:
            for message in messages:
                msg = self.service_gmail.users().messages().get(userId="me", id=message["id"]).execute()
                payload = msg["payload"]
                headers = payload.get("headers", [])
                
                # Extract Subject and Sender
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
                
                # Get the snippet (short preview)
                snippet = msg.get("snippet", "")

                print(f"📧 Found: {subject} | From: {sender}")
                
                email_data.append({
                    "id": message["id"],
                    "subject": subject,
                    "sender": sender,
                    "snippet": snippet
                })
        
        return email_data
    
    def log_to_sheet(self, data):
        """
        Appends the analyzed data to the Google Sheet.
        data: An instance of the EmailAnalysis class (from llm_brain.py)
        """
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        
        # The data we want to save (Row format)
        values = [[
            data.customer_name,
            data.order_id,
            data.category,
            data.sentiment,
            data.summary
        ]]

        body = {
            'values': values
        }

        try:
            result = self.service_sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A:E",  # Adjust 'Sheet1' if your tab has a different name
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            print(f"✅ Logged to Sheet: {result.get('updates').get('updatedCells')} cells updated.")
        except Exception as e:
            print(f"❌ Sheet Error: {e}")

# --- TESTING BLOCK ---
# This allows you to run this file directly to test it.
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Load the .env file so we can get SPREADSHEET_ID

    try:
        manager = EmailManager()
        
        # 1. Test Gmail
        print("--- Testing Gmail ---")
        manager.fetch_recent_emails(count=1)
        
        # 2. Test Sheets
        print("\n--- Testing Sheets ---")
        
        # Create a fake object to simulate the Brain's output
        class DummyAnalysis:
            customer_name = "TEST USER"
            order_id = "TEST-999"
            category = "Testing"
            sentiment = "Neutral"
            summary = "This is a test row generated by the connection script."

        manager.log_to_sheet(DummyAnalysis())
        
        print("\n✅ SUCCESS: Connected to Gmail AND Google Sheets!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")