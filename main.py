import os
import shutil
from google.cloud import texttospeech
from pydub import AudioSegment

def split_text(text, max_length=3000):
    paragraphs = text.split('\n')
    current_chunk = ""
    chunks = []
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= max_length:
            current_chunk += paragraph + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def synthesize_speech(text, output_file, voice_name="en-IN-Standard-B", speaking_rate=0.75):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate  # Use the speaking rate parameter
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file, 'wb') as file:
        file.write(response.audio_content)

def concatenate_audios(audio_files, output_file):
    combined = AudioSegment.empty()
    for file in audio_files:
        combined += AudioSegment.from_mp3(file)
    
    combined.export(output_file, format="mp3")

def text_to_speech(text_file, output_file, voice_name="en-IN-Standard-B", speaking_rate=0.75):
    with open(text_file, 'r') as file:
        text = file.read()
    
    text_chunks = split_text(text)
    
    temp_dir = "temp_audio_chunks"
    os.makedirs(temp_dir, exist_ok=True)
    
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        chunk_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
        synthesize_speech(chunk, chunk_file, voice_name, speaking_rate)
        audio_files.append(chunk_file)
    
    concatenate_audios(audio_files, output_file)
    
    # Clean up temporary files and directory
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    chapter = '22'
    text_file = 'input/tripura_rahasya_english_final/chapter_' + chapter + '.txt'  # Replace with your text file
    output_file = 'output/tripura_rahasya_english_final_audiobook/chapter_' + chapter + '.mp3'  # Output audio file
    text_to_speech(text_file, output_file, voice_name="en-IN-Wavenet-B", speaking_rate=0.6)  # Use desired voice name and speaking rate
    print(f'Audiobook saved as {output_file}')