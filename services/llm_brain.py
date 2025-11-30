import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API (New SDK)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- 1. Define the "Form" (MERGED: Old + New Fields) ---
class EmailAnalysis(BaseModel):
    # --- EXISTING FEATURES ---
    sentiment: str = Field(description="The sentiment: 'Positive', 'Negative', or 'Neutral'")
    customer_name: str = Field(description="Customer Name. If unknown, use 'Unknown'.")
    order_id: str = Field(description="Order ID (e.g., #12345) or 'N/A'.")
    category: str = Field(description="Category: 'Delivery', 'Product', 'Refund', 'General', 'Spam'")
    summary: str = Field(description="1-sentence summary for a busy manager.")
    
    # --- NEW WINNING FEATURES ---
    tone: str = Field(description="The emotional tone (e.g., 'Frustrated', 'Polite', 'Urgent', 'Sarcastic').")
    recommendation: str = Field(description="The next best action (e.g., 'Offer discount', 'Check tracking', 'Reply').")

# --- 2. The Brain Function ---
def analyze_email(email_text):
    """
    Sends email text to Gemini and returns a structured EmailAnalysis object.
    """
    try:
        # We use standard 2.5 Flash (Most reliable for Hackathons)
        prompt = f"""
        You are an elite Customer Experience AI. 
        Analyze the following customer email. 
        Identify the core Details, the Emotional Tone, and suggest a Next Best Action.
        
        EMAIL CONTENT:
        "{email_text}"
        """

        # detailed instruction to force the specific JSON structure
        response = client.models.generate_content(
            model="gemini-2.5-flash", # Switched to 1.5-flash to ensure stability
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
            summary="Could not analyze this email.",
            tone="Neutral",                # Default for error
            recommendation="Check manually" # Default for error
        )
    
def generate_email_reply(customer_name, issue_summary, sentiment):
    """
    Generates a polite, professional email response.
    """
    try:
        prompt = f"""
        You are a Customer Service Agent. Write a short, professional email reply to {customer_name}.
        
        Context:
        - The customer is feeling: {sentiment}
        - Their issue was: "{issue_summary}"
        
        Rules:
        - If Negative, be apologetic and offer help.
        - If Positive, thank them.
        - Keep it under 50 words.
        - Do not include subject line or placeholders like [Your Name].
        """
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return f"Dear {customer_name},\n\nThank you for your feedback. We are looking into it.\n\nBest,\nSupport Team"

# ... existing code ...

def translate_to_hindi(text):
    """Translates a short summary into Hindi/Hinglish for voice."""
    try:
        prompt = f"Translate this customer service summary into natural conversational Hindi (Hinglish) for a voice assistant to speak:\n\n'{text}'"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return text # Fallback to English

# --- TESTING BLOCK ---
if __name__ == "__main__":
    test_email = """
    Subject: Broken Item
    From: Sarah Connor
    Hi, I received my order #998877 yesterday, but the package was crushed. 
    I am very unhappy with this delivery service! Please refund me.
    """
    
    print("🧠 Thinking...")
    result = analyze_email(test_email)
    
    print("\n--- Analysis Result ---")
    print(f"Name:           {result.customer_name}")
    print(f"Sentiment:      {result.sentiment}")
    print(f"Tone:           {result.tone}  <-- NEW")
    print(f"Recommendation: {result.recommendation}  <-- NEW")
    print(f"Summary:        {result.summary}")