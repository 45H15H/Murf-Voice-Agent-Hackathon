import os
import requests
import pyaudio
from dotenv import load_dotenv

load_dotenv()

class VoiceEngine:
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        self.voice_id = os.getenv("MURF_VOICE_ID", "en-US-natalie")
        self.url = "https://global.api.murf.ai/v1/speech/stream"

        # Audio Config for Falcon (Standard is 24kHz)
        self.sample_rate = 24000
        self.channels = 1
        self.format = pyaudio.paInt16  # PCM Format

    def speak(self, text):
        """
        Sends text to Murf Falcon and streams the audio output immediately.
        """
        if not text:
            return

        print(f"🗣️ Speaking: {text}")

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            # "Accept": "application/json"
        }

        # The Falcon Payload
        payload = {
            "text": text,
            "model": "FALCON",          # CRITICAL: Forces the low-latency model
            "voice_id": self.voice_id,
            "multi_native_locale": "en-US",
            "format": "PCM",            # We want raw audio bytes for faster playback
            "sampleRate": self.sample_rate,
            "channelType": "MONO"
        }

        try:
            # 1. Send Request to Murf
            response = requests.post(self.url, headers=headers, json=payload, stream=True)
            
            if response.status_code != 200:
                print(f"❌ Murf API Error: {response.status_code} - {response.text}")
                return

            # 2. Setup Audio Player (PyAudio)
            p = pyaudio.PyAudio()
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True
            )

            # 3. Stream the audio chunks as they arrive
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    stream.write(chunk)

            # 4. Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            print(f"❌ Voice Error: {e}")

# --- TESTING BLOCK ---
if __name__ == "__main__":
    bot = VoiceEngine()
    bot.speak("System initialized. I am ready to process your emails.")