from openai import OpenAI
from file_util import find_new_file_name

client = OpenAI()

def create_translation(recording, model="whisper-1", saveOutput=False) -> str:
    '''
    Returns string transcription of an audio file, translated into English. Uses OpenAI API.

    Args:
        Audio file path (str), LLM to use (str), Save output to a text file (bool)

    Returns:
        String transcription (English) of the speech in the audio file
    '''
    print ("--- Transcribing... ---")

    with open (recording, "rb") as audio_file:
        try:
            transcription = client.audio.translations.create(
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
    
def create_transcription(recording, model="gpt-4o-transcribe", saveOutput=False) -> str:
    '''
    Returns string transcription of an audio file in spoken language. Uses OpenAI API.

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