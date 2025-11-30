import os
import wave
import pyaudio
import assemblyai as aai
import threading
import time
from dotenv import load_dotenv

load_dotenv()

class Transcriber:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        aai.settings.api_key = self.api_key
        
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.OUTPUT_FILENAME = "command.wav"
        
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.p = None

    def start_recording(self):
        """Starts recording audio in a background thread."""
        self.frames = []
        self.is_recording = True
        self.p = pyaudio.PyAudio()
        
        # Open stream
        self.stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        
        # Start the listener thread
        threading.Thread(target=self._record_loop, daemon=True).start()
        print("🔴 Recording started...")

    def _record_loop(self):
        """Internal loop to grab audio chunks."""
        while self.is_recording:
            try:
                # 'exception_on_overflow' prevents crashes if CPU is busy
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception:
                # If stream is closed externally, just exit the loop safely
                break

    def stop_recording(self):
        """Stops recording, saves file, and returns the transcript."""
        print("⏹️ Stopping recording...")
        
        # 1. Signal loop to stop
        self.is_recording = False
        
        # 2. Safety Buffer: Wait 0.2s for the thread to finish its last read
        time.sleep(0.2) 
        
        # 3. Cleanup Audio Resources safely
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
        except Exception as e:
            print(f"Warning during audio cleanup: {e}")

        # 4. Save File
        try:
            wf = wave.open(self.OUTPUT_FILENAME, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return ""

        # 5. Transcribe
        print("📝 Transcribing...")
        return self._transcribe_file()

    def _transcribe_file(self):
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(self.OUTPUT_FILENAME)
            
            if transcript.status == aai.TranscriptStatus.error:
                return f"Error: {transcript.error}"
            
            return transcript.text or ""
        except Exception as e:
            return f"Error: {e}"