import os
import wave
import pyaudio
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()

class Transcriber:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY missing in .env")
        
        # Configure AssemblyAI
        aai.settings.api_key = self.api_key
        
        # Audio Recording Config
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.RECORD_SECONDS = 5
        self.OUTPUT_FILENAME = "command.wav"

    def listen(self):
        """
        Records audio for 5 seconds and transcribes it using AssemblyAI.
        """
        print(f"👂 Listening for {self.RECORD_SECONDS} seconds...")
        
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

        frames = []

        # 1. Record Audio
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            frames.append(data)

        print("✅ Recording complete. Transcribing...")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save to file locally
        wf = wave.open(self.OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # 2. Send to AssemblyAI
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(self.OUTPUT_FILENAME)

            if transcript.status == aai.TranscriptStatus.error:
                print(f"❌ Transcription Error: {transcript.error}")
                return ""

            text = transcript.text
            print(f"📝 You said: '{text}'")
            return text

        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            return ""

# --- TEST BLOCK ---
if __name__ == "__main__":
    ear = Transcriber()
    input("Press Enter to start recording...")
    text = ear.listen()