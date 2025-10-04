from utils.openai_utils import create_transcription
from queue import Queue
from pynput import keyboard
from utils.audio_util import Push_to_talk
from utils.comfy_api import Comfy
import time
import threading

'''
Program for generating images from user sound input using OpenAI transcription API and ComfyUI API calls
Can also be used with other image generation API:s with a bit of tweaking
'''
# Create a processing queue for the transcriptions
transcribe_queue = Queue()

# If left shift is pressed, start recording
def on_press(recorder, key):
        try:
            if key == keyboard.Key.shift:
                recorder.start_recording()
        except AttributeError:
            pass
    
# If left shift is released, stop recording, generate transcription and push it in the queue
def on_release(recorder, key):
    try:
        if key == keyboard.Key.shift:
            filename = recorder.stop_recording()
            if filename:
                def worker(filename, model, saveOutput, removeFile):
                    transcript = create_transcription(filename, model, saveOutput, removeFile)
                    transcribe_queue.put(transcript)

                threading.Thread(target=worker, args=[filename,"gpt-4o-transcribe",False,True]).start()  # By default delete audio files after creating transcriptions, and don't save output on a separate file
    except AttributeError:
        pass

# Orchestration function for recording, API calls etc.
def main():
    print("Voice-controlled image generator using ComfyUI API")
    try:
        recorder = Push_to_talk(device=12, samplerate=48000, channels=1)  # New recorder object
        print("Voice recorder ready!")
    except Exception as e:
        print(f"Error creating the recorder instance. Make sure the recorder class exists: {e}")
    try:
        comfy_client = Comfy(workflow_path="sdxlturbo_example.json")  # ComfyUI client instance
        print("Connected to ComfyUI Client!")
    except Exception as e:
        print(f"Error connecting to ComfyUI Client. Make sure the client is running and the class exists {e}")
        exit
    listener = keyboard.Listener(  
        on_press= lambda key: on_press(recorder, key),
        on_release=lambda key: on_release(recorder, key)
    )
    listener.start() # Activate keyboard listener
    print("Press shift to record audio for image prompt, ctrl+c to quit:")

    try:
        while True:

            # check queue
            while not transcribe_queue.empty():
                prompt = transcribe_queue.get()
                # If a prompt is found in the transcription queue, send to comfy_client
                if isinstance(prompt, str) and prompt.strip():
                    print(f"Prompt: {prompt}")
                    comfy_client.get_image(prompt, "lowres, low quality")
                else:
                    print("Generating prompt failed, please try again: ")
                print("Press shift to record audio for image prompt, ctrl+c to quit:")

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()