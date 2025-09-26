from openai import OpenAI
from queue import Queue
from audio_util import Push_to_talk
from pynput import keyboard
from openai_utils import create_translation
import time
import threading

transcribe_queue = Queue()

def on_press(recorder, key):
        try:
            if key == keyboard.Key.shift:
                recorder.start_recording()
        except AttributeError:
            pass
    
def on_release(recorder, key):
    try:
        if key == keyboard.Key.shift:
            filename = recorder.stop_recording()
            if filename:
                def worker(filename, model, saveOutput):
                    transcript = create_translation(filename, model, saveOutput)
                    transcribe_queue.put(transcript)

                threading.Thread(target=worker, args=[filename,"whisper-1",True]).start()
    except AttributeError:
        pass
    


def main():
    recorder = Push_to_talk(device=12, samplerate=48000, channels=1)  # New recorder object
    listener = keyboard.Listener(  
        on_press= lambda key: on_press(recorder, key),
        on_release=lambda key: on_release(recorder, key)
    )
    listener.start() # Activate keyboard listener

    try:
        while True:
            # check queue
            while not transcribe_queue.empty():
                audio_file = transcribe_queue.get()
                print(audio_file)

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()