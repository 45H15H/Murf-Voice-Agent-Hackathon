import time
from services.email_manager import EmailManager
from services.llm_brain import analyze_email
from services.murf_tts import VoiceEngine
from services.transcriber import Transcriber

def main():
    # 1. Initialize the Hardware
    print("🔌 Initializing services...")
    voice = VoiceEngine()
    ears = Transcriber()
    
    # 2. Welcome Sequence
    print("🤖 Agent Online")
    voice.speak("System online. I am your feedback assistant. Say 'Start' to begin analysis, or 'Exit' to quit.")

    # 3. Main Listening Loop
    while True:
        # The agent listens for 5 seconds
        command = ears.listen() 
        
        # Sanitize input (handle empty audio or noise)
        if not command:
            print("... No distinct speech detected ...")
            continue

        command = command.lower()

        # Command: START
        if "start" in command or "begin" in command or "analyze" in command:
            voice.speak("Understood. Scanning your inbox now.")
            run_analysis_workflow(voice)
            
            # Reset and wait for next command
            voice.speak("I am ready for the next command.")
        
        # Command: EXIT
        elif "exit" in command or "stop" in command or "quit" in command:
            voice.speak("Shutting down. Goodbye.")
            break
        
        # Unknown Command
        else:
            print(f"Ignored command: {command}")
            voice.speak("I didn't catch that. Please say Start or Exit.")

def run_analysis_workflow(voice):
    """
    Executes the core business logic: Fetch -> Analyze -> Save -> Report
    """
    try:
        # Initialize Email Manager (Connects to Gmail/Sheets)
        email_bot = EmailManager()
        
        # Fetch last 3 emails (Adjust this number as needed)
        emails = email_bot.fetch_recent_emails(count=3)

        if not emails:
            voice.speak("I did not find any new emails.")
            return

        voice.speak(f"I found {len(emails)} recent emails.")

        # Tracking variables for the final report
        negative_count = 0
        high_priority_summaries = []

        # Process each email
        for mail in emails:
            print(f"   > Analyzing: {mail['subject']}...")
            
            # Prepare text for the Brain
            full_text = f"Subject: {mail['subject']}\nFrom: {mail['sender']}\nContent: {mail['snippet']}"
            
            # A. BRAIN: Analyze Sentiment
            analysis = analyze_email(full_text)
            
            # B. SHEETS: Log Data
            email_bot.log_to_sheet(analysis)

            # C. MEMORY: Track critical issues
            if analysis.sentiment == "Negative":
                negative_count += 1
                high_priority_summaries.append(f"From {analysis.customer_name}: {analysis.summary}")

        # Final Verbal Report
        if negative_count == 0:
            voice.speak("Analysis complete. All recent feedback was positive or neutral.")
        else:
            voice.speak(f"Alert. I found {negative_count} negative reviews.")
            voice.speak("Here is the summary of the critical issues.")
            
            for summary in high_priority_summaries:
                voice.speak(summary)
                time.sleep(0.5) # Natural pause between items

        voice.speak("All data has been logged to the dashboard.")

    except Exception as e:
        print(f"❌ Workflow Error: {e}")
        voice.speak("I encountered an error while processing the emails.")

if __name__ == "__main__":
    main()