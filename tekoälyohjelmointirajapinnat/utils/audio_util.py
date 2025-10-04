import sounddevice as sd
import soundfile as sf
import numpy as np
import time

class Push_to_talk:
    """
    A push-to-talk audio recording utility class.
    This class provides functionality to record audio from a specified input device
    and save it as a WAV file when recording is stopped.
    Attributes:
        device (int): Audio input device index (default: 12)
        samplerate (int): Audio sample rate in Hz (default: 48000)
        channels (int): Number of audio channels (default: 1)
        recording (bool): Current recording state
        frames (list): List to store audio frame data during recording
        stream (sd.InputStream): SoundDevice input stream object
    Methods:
        start_recording(): Begins audio recording from the specified device
        stop_recording(): Stops recording and saves audio to a timestamped WAV file
        audio_callback(): Callback function to handle incoming audio data
    Example:
        recorder = Push_to_talk(device=12, samplerate=48000, channels=1)
        recorder.start_recording()
        # ... recording happens while method is active ...
        filename = recorder.stop_recording()  # Returns saved filename
    """
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
            self.stream = sd.InputStream(
                samplerate=self.samplerate, 
                channels=self.channels, 
                dtype='float32',
                callback=self.audio_callback
            )
            self.stream.start()
            print("Recording... Release LEFT SHIFT to stop.")

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
    