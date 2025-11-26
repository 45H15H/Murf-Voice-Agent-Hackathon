import time
from services.email_manager import EmailManager
from services.llm_brain import analyze_email
from services.murf_tts import VoiceEngine

def main():
    # 1. Initialize the Organs
    print("🔌 Initializing services...")
    voice = VoiceEngine()
    email_bot = EmailManager()

    # 2. Welcome Message
    print("🤖 Agent Started")
    voice.speak("System online. I am scanning your inbox for customer feedback.")

    # 3. Fetch Emails
    emails = email_bot.fetch_recent_emails(count=3) # limiting to 3 for testing

    if not emails:
        voice.speak("I did not find any new emails.")
        return

    voice.speak(f"I found {len(emails)} recent emails. Processing them now.")

    # 4. Processing Loop
    negative_count = 0
    high_priority_summaries = []

    for mail in emails:
        print(f"   > Analyzing: {mail['subject']}...")
        
        # A. The Brain works
        # We combine subject + snippet for better context
        full_text = f"Subject: {mail['subject']}\nFrom: {mail['sender']}\nContent: {mail['snippet']}"
        analysis = analyze_email(full_text)

        # B. The Spreadsheet works
        email_bot.log_to_sheet(analysis)

        # C. Track stats for the verbal report
        if analysis.sentiment == "Negative":
            negative_count += 1
            # Save the summary to read it out loud later
            high_priority_summaries.append(f"From {analysis.customer_name}: {analysis.summary}")

    # 5. Final Voice Report
    voice.speak("Analysis complete.")
    
    if negative_count == 0:
        voice.speak("Good news. All feedback was positive or neutral.")
    else:
        voice.speak(f"Alert. I found {negative_count} negative reviews.")
        voice.speak("Here is the summary of the critical issues.")
        
        for summary in high_priority_summaries:
            voice.speak(summary)
            time.sleep(0.5) # clear pause between items

    voice.speak("All data has been logged to the dashboard.")

if __name__ == "__main__":
    main()