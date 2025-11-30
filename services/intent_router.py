import os
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class UserIntent(BaseModel):
    # CHANGED: 'SUMMARIZE_HINDI' -> 'SUMMARIZE_SPECIFIC'
    action: str = Field(description="Action: 'ANALYZE_NEW', 'GET_SENTIMENT_STATS', 'SUMMARIZE_SPECIFIC', 'FILTER_BY_CATEGORY', 'DRAFT_REPLY', 'EXIT', 'UNKNOWN'")
    keywords: str = Field(description="Specific targets (e.g., 'delivery', 'email 4', 'Sarah'). If none, use 'none'.")
    language: str = Field(description="Language requested: 'en' for English, 'hi' for Hindi. Default to 'en'.")

def determine_intent(user_text):
    try:
        prompt = f"""
        You are the Brain of a Voice Agent. Extract Action, Keywords, and Language.
        
        ACTIONS:
        - ANALYZE_NEW: Fetch/scan emails. (e.g. "Start analysis", "Check inbox", "Scan in Hindi")
        - GET_SENTIMENT_STATS: Stats report. (e.g. "How is the mood?", "Stats")
        
        # --- CHANGED: Neutral Action Name ---
        - SUMMARIZE_SPECIFIC: Explain/Read a SPECIFIC email. (e.g. "Explain email 4", "Read number 2", "Explain email 2 in Hindi")
        
        - FILTER_BY_CATEGORY: Filter topic. (e.g. "Show delivery emails")
        - DRAFT_REPLY: Write email. (e.g. "Draft reply to #3")
        - EXIT: Stop/Quit.

        LANGUAGE RULES:
        - If "Hindi" is explicitly mentioned, set language='hi'.
        - If "Hindi" is NOT mentioned, set language='en'.
        
        KEYWORDS RULES:
        - If user mentions a number or name (e.g. "email 4", "Sarah"), put "4" or "Sarah" in keywords.
        
        User Command: "{user_text}"
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": UserIntent}
        )

        return UserIntent.model_validate_json(response.text)

    except Exception as e:
        print(f"Router Error: {e}")
        return UserIntent(action="UNKNOWN", keywords="none", language="en")