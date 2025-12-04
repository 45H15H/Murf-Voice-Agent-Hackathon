import os
import requests
import pyaudio
from dotenv import load_dotenv
import re

load_dotenv()

class VoiceEngine:
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        self.url = "https://global.api.murf.ai/v1/speech/stream"
        
        # Audio Config
        self.sample_rate = 24000
        self.channels = 1
        self.format = pyaudio.paInt16

    def _sanitize_text(self, text):
        """Cleans text to prevent TTS static/artifacts."""
        if not text: return ""
        
        # 1. Replace double/triple dots with a single dot
        text = re.sub(r'\.{2,}', '.', text)
        
        # 2. Fix "Action.. Recommendation" issues
        text = text.replace("..", ".")
        
        # 3. Smooth out the "Recommendation:" transition
        # Instead of a sharp colon, we make it a sentence flow which sounds better
        text = text.replace("Recommendation:", "My recommendation is")
        
        # 4. Remove weird extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def speak(self, text, language_code="en"):
        """
        Speaks text using Murf.
        - English: Uses 'Natalie'
        - Hindi: Uses 'Namrita' (hi-IN-namrita)
        """
        if not text: return


        # --- CLEAN THE TEXT BEFORE SENDING ---
        clean_text = self._sanitize_text(text)
        print(f"🗣️ Speaking ({language_code}): {clean_text}")

        # --- 1. VOICE SELECTION ---
        if language_code == "hi":
            selected_voice = "hi-IN-namrita"
            # Namrita is native Hindi, so we usually don't need to force the locale
            # But we leave en-US as base just in case
            locale = "hi-IN" 
        else:
            selected_voice = "en-US-natalie"
            locale = "en-US"

        # --- 2. HEADER FIX (Removed 'Accept' to fix 406 Error) ---
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # --- 3. PAYLOAD ---
        # Note: If Namrita is NOT a Falcon voice, you might need to change model to "GEN2"
        # But for the hackathon, we keep "FALCON" and hope she is supported.
        payload = {
            # "text": text,
            "text": clean_text,
            "model": "FALCON",
            "voiceId": selected_voice,
            "multiNativeLocale": locale,
            "format": "PCM",
            "sampleRate": self.sample_rate,
            "channelType": "MONO"
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, stream=True)
            
            if response.status_code != 200:
                print(f"❌ Murf API Error: {response.status_code} - {response.text}")
                return

            # --- 4. STREAM AUDIO ---
            p = pyaudio.PyAudio()
            stream = p.open(format=self.format, channels=self.channels, rate=self.sample_rate, output=True)

            audio_buffer = bytearray()
            MIN_CHUNK_SIZE = 4096 

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_buffer.extend(chunk)
                    
                    # While we have enough data in the buffer, write it out
                    while len(audio_buffer) >= MIN_CHUNK_SIZE:
                        # Take the first 4096 bytes
                        data_to_play = audio_buffer[:MIN_CHUNK_SIZE]
                        stream.write(bytes(data_to_play))
                        
                        # Remove them from the buffer
                        del audio_buffer[:MIN_CHUNK_SIZE]

            # Play whatever is left in the buffer at the end
            if len(audio_buffer) > 0:
                stream.write(bytes(audio_buffer))

            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            print(f"❌ Voice Error: {e}")

# --- TEST BLOCK ---
if __name__ == "__main__":
    bot = VoiceEngine()
    print("Testing English...")
    bot.speak("System check. English voice is active.")
    
    print("\nTesting Hindi...")
    bot.speak("नमस्ते, सिस्टम चेक सफल रहा।", language_code="hi")