from openai import OpenAI
import sounddevice as sd
import time
from utils.file_util import find_new_file_name
import soundfile as sf
import argparse

client = OpenAI()

def recordSpeech(seconds, device=12, samplerate=48000, channels=1):
    sd.default.device=device
    seconds = seconds  # Duration of recording
    print ("--- Recording... ---")
    data = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=channels)
    for n in range(seconds, 0, -1):  # Countdown timer
        print(n)
        time.sleep(1)

    sd.wait()  # Wait until recording is finished
    print ("Recording done")
    filenameRecording=find_new_file_name("speech.wav")

    sf.write(filenameRecording, data, samplerate, subtype="PCM_16")
    print(f"Saved input to: {filenameRecording}\n")
    return filenameRecording
    

def createTranscription(recording, model="gpt-4o-transcribe", saveOutput=False) -> str:
    '''
    Returns string transcription of an audio file. Uses OpenAI API.

    Args:
        Audio file path (str), LLM to use (str), Save output to a text file (bool)

    Returns:
        String transcription of the speech in the audio file
    '''
    print ("--- Transcribing... ---")

    with open (recording, "rb") as audio_file:
        try:
            transcription = client.audio.transcriptions.create(
            model=model, 
            file=audio_file,
            )
            print(f'Transcription: {transcription.text}\n')
            if saveOutput:
                filename = find_new_file_name("transcription.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcription.text)
                    print(f"Final output saved to {filename}")
        except Exception as e:
            print(f'Error creating transcription: {e}')
            return None
        return transcription.text

    
def translate(transcription, lang):
    try:
        print(f"--- Translating into following language: {lang} ---")
        response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=f"Translate the following text into {lang}.",
        input=transcription
        )
        print(f"Translation: {response.output_text}\n")
    except Exception as e:
        print(f'Error creating transcription: {e}')
        return None
    return response.output_text

def createTTS(translation, recording):
    print("--- Generating TTS: ---")
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy", # alloy, echo, fable, onyx, nova, and shimmer
    input=translation,
    response_format="wav",
    )
    with open(recording, "wb") as f:
        f.write(response.read())
    print(f"Translation saved to: {recording}\n")
    return recording

'''
def playTTS(ttsFilename):
    data, samplerate = sf.read(ttsFilename, dtype="float32")
    sd.play(data, samplerate)
    sd.wait()
'''

def main():
    parser = argparse.ArgumentParser(
        prog="Voice interpreter",
        description="Translates spoken voice to another language"
    )
    parser.add_argument("-l", "--language", type=str, default="en", help="Language which the speech will be translated to")
    parser.add_argument("-d", "--duration", type=int, default=10, choices=[5,10,20], help="Duration of the speech input")
    # parser.add_argument("-p", "--playback", action='store_true', default=False, help="Option to play the TTS translation automatically")
    parser.add_argument("--device", type=int, default=None, help="sounddevice device index (optional)")
    args = parser.parse_args()

    recording = recordSpeech(args.duration)
    start= time.perf_counter()
    transcription = createTranscription(recording)
    translation = translate(transcription, args.language)
    tts = createTTS(translation, recording)
    end=time.perf_counter()
    duration = end - start
    print(f"Total time for response: {duration:.2f} seconds")
    '''
    if args.playback:
        playTTS(tts)
    '''
if __name__=="__main__":
    main()