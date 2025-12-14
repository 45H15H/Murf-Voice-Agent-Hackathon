# 🎙️ InboxPilot (Customer Feedback Agent)
### Built for the Murf Voice Agent Hackathon 2025

**Turn your Inbox into a Conversation.**

This project is a fully functional **Voice AI Agent** that automates customer service operations. Instead of reading through hundreds of emails, a manager can simply *talk* to their dashboard to analyze sentiment, filter urgency, and even draft replies—all hands-free.

Powered by **Murf Falcon** for ultra-low latency, lifelike speech.

## 🚀 Key Features

### 1. 🗣️ Conversational Intelligence
* **Natural Voice Commands:** "Start analysis", "Show me delivery complaints", "How is the mood today?"
* **Smart Intent Router:** Uses Gemini to understand context (e.g., distinguishing between "Explain email 2" vs "Draft reply to email 2").

### 2. ⚡ Powered by Murf Falcon
* **Zero-Latency Response:** Utilizes Murf's Falcon model to generate speech instantly, making the conversation feel real.
* **Multi-Voice & Multi-Language:** * *English Mode:* Uses **Natalie (US)** for crisp professional reporting.
    * *Hindi Mode:* Seamlessly switches to **Namrita** when asked "Explain this in Hindi" (Code Switching).

### 3. 🧠 Advanced Analysis (The "Brain")
* **Sentiment & Tone Detection:** Classifies emails as Positive/Neutral/Negative and detects emotions like "Frustrated" or "Urgent".
* **Next-Best-Action:** The AI suggests what to do (e.g., "Recommend offering a full refund").

### 4. ✍️ Voice-to-Action Automation
* **Draft Replies:** Say "Draft a reply to email #3", and the agent writes a polite, context-aware email and saves it to your Gmail Drafts folder using the Gmail API.

---

## 🛠️ Tech Stack

* **Voice Generation:** Murf Falcon API (Text-to-Speech)
* **Hearing (ASR):** AssemblyAI (Speech-to-Text)
* **Intelligence:** Google Gemini 2.5 Flash (LLM)
* **Interface:** Python Flet (Modern UI)
* **Automation:** Google Gmail API & Sheets API

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/voice-feedback-agent.git](https://github.com/YOUR_USERNAME/voice-feedback-agent.git)
cd voice-feedback-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the root directory and add your API keys:
```
MURF_API_KEY=your_murf_key
MURF_VOICE_ID=en-US-natalie
ASSEMBLYAI_API_KEY=your_assembly_key
GEMINI_API_KEY=your_gemini_key
SPREADSHEET_ID=your_google_sheet_id
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### 4. Google Cloud Setup
1. Enable Gmail API and Google Sheets API in Google Cloud Console.
2. Download credentials.json (OAuth Desktop Client) and place it in the root folder.
3. On first run, it will open a browser to authorize access.

### 5. Run the Application
```bash
python gui_app.py
```
