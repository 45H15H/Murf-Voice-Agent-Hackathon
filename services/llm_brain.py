import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- 1. Define the "Form" we want Gemini to fill out ---
class EmailAnalysis(BaseModel):
    sentiment: str = Field(description="The sentiment of the email: 'Positive', 'Negative', or 'Neutral'")
    customer_name: str = Field(description="The name of the customer found in the email signature or header. If unknown, use 'Unknown'.")
    order_id: str = Field(description="The Order ID if mentioned (e.g., #12345). If not found, use 'N/A'.")
    category: str = Field(description="Category of the issue: 'Delivery', 'Product Quality', 'Refund', 'General Inquiry', or 'Spam'")
    summary: str = Field(description="A very short 1-sentence summary of the email for a busy manager.")

# --- 2. The Brain Function ---
def analyze_email(email_text):
    """
    Sends email text to Gemini and returns a structured EmailAnalysis object.
    """
    try:
        # We use Gemini 2.5 Flash because it's fast and cheap for hackathons
        # model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are a Customer Service Manager AI. 
        Analyze the following customer email and extract the key details.
        
        EMAIL CONTENT:
        "{email_text}"
        """

        # detailed instruction to force the specific JSON structure
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EmailAnalysis
            }
        )

        # Gemini returns a JSON string, which we convert back to our Python object
        analysis = EmailAnalysis.model_validate_json(response.text)
        return analysis

    except Exception as e:
        print(f"❌ Brain Error: {e}")
        # Return a "dummy" analysis so the app doesn't crash
        return EmailAnalysis(
            sentiment="Neutral", 
            customer_name="Unknown", 
            order_id="Error", 
            category="Error", 
            summary="Could not analyze this email."
        )

# --- TESTING BLOCK ---
if __name__ == "__main__":
    # Fake email to test the brain
    test_email = """
    Subject: Broken Item
    From: Sarah Connor
    Hi, I received my order #998877 yesterday, but the package was crushed. 
    I am very unhappy with this delivery service! Please refund me.
    """
    
    print("🧠 Thinking...")
    result = analyze_email(test_email)
    
    print("\n--- Analysis Result ---")
    print(f"Sentiment: {result.sentiment}")
    print(f"Name:      {result.customer_name}")
    print(f"Order ID:  {result.order_id}")
    print(f"Category:  {result.category}")
    print(f"Summary:   {result.summary}")