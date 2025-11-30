import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# New SDK Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Define the "Moves" your agent can make
class UserIntent(BaseModel):
    action: str = Field(description="The strict action name. Options: 'ANALYZE_NEW', 'GET_SENTIMENT_STATS', 'SUMMARIZE_HINDI', 'EXIT', 'UNKNOWN'")
    keywords: str = Field(description="Key topics mentioned (e.g., 'delivery', 'urgent', 'broken'). If none, use 'none'.")

def determine_intent(user_text):
    """
    Decides what the user wants to do based on their voice command.
    """
    try:
        prompt = f"""
        You are the Routing System for a Voice Agent. Map the user's command to one of these actions:
        
        - ANALYZE_NEW: User wants to check, read, or scan recent emails. (e.g., "Check inbox", "Start analysis", "Any new mail?")
        - GET_SENTIMENT_STATS: User wants a high-level summary or stats. (e.g., "How are customers feeling?", "Give me a report", "What's the mood?")
        - SUMMARIZE_HINDI: User specifically asks to speak/summarize in Hindi. (e.g., "Say that in Hindi", "Tell me in Hindi")
        - FILTER_BY_CATEGORY: User wants to hear about specific issues. (e.g. "Show me delivery emails", "Any complaints about products?", "Read refund requests").
          -> IMPORTANT: Put the category name (Delivery, Product, Refund) in the 'keywords' field.
        - EXIT: User wants to stop/quit.
        - UNKNOWN: Command is unclear or unrelated.

        User Command: "{user_text}"
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": UserIntent
            }
        )

        return UserIntent.model_validate_json(response.text)

    except Exception as e:
        print(f"🧠 Router Error: {e}")
        return UserIntent(action="UNKNOWN", keywords="none")