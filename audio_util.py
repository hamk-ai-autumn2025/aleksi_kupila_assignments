import sounddevice as sd
import soundfile as sf
import numpy as np
import time
from pynput import keyboard

class Push_to_talk:
    def __init__(self, device=12, samplerate=48000, channels=1):
        self.device = device
        self.samplerate = samplerate
        self.channels = channels
        self.recording = False
        self.frames = []
        self.stream = None
        sd.default.device = device
        
    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            print("Recording... Release LEFT SHIFT to stop.")
            self.stream = sd.InputStream(
                samplerate=self.samplerate, 
                channels=self.channels, 
                dtype='float32',
                callback=self.audio_callback
            )
            self.stream.start()

    def stop_recording(self):
        if self.recording:
            self.recording = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
            
            if self.frames:
                audio = np.concatenate(self.frames, axis=0)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.wav"
                sf.write(filename, audio, self.samplerate)
                print(f"Saved: {filename}")
                return filename
    
    def audio_callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())
    