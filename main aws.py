import boto3
import os
import shutil
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

def synthesize_speech(text, output_file, voice_id="Matthew", profile_name="chillpanda"):
    session = boto3.Session(profile_name=profile_name)
    polly_client = session.client('polly')
    
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=voice_id
    )

    with open(output_file, 'wb') as file:
        file.write(response['AudioStream'].read())

def change_audio_speed(input_file, output_file, speed=0.75):
    audio = AudioSegment.from_file(input_file)
    slowed_audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * speed)
    }).set_frame_rate(audio.frame_rate)
    slowed_audio.export(output_file, format="mp3")

def concatenate_audios(audio_files, output_file):
    combined = AudioSegment.empty()
    for file in audio_files:
        combined += AudioSegment.from_mp3(file)
    
    combined.export(output_file, format="mp3")

def text_to_speech(text_file, output_file, voice_id="Matthew", profile_name="chillpanda"):
    with open(text_file, 'r') as file:
        text = file.read()
    
    text_chunks = split_text(text)
    
    temp_dir = "temp_audio_chunks"
    os.makedirs(temp_dir, exist_ok=True)
    
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        chunk_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
        synthesize_speech(chunk, chunk_file, voice_id, profile_name)
        
        slowed_chunk_file = os.path.join(temp_dir, f"slowed_chunk_{i}.mp3")
        change_audio_speed(chunk_file, slowed_chunk_file, speed=0.9)
        audio_files.append(slowed_chunk_file)
    
    concatenate_audios(audio_files, output_file)
    
    # Clean up temporary files and directory
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    text_file = 'input/tripura_rahasya_english_final/chapter_1.txt'  # Replace with your text file
    output_file = 'output/tripura_rahasya_english_final_audiobook/chapter_1.mp3'  # Output audio file
    text_to_speech(text_file, output_file, voice_id="Brian")  # Use desired voice ID
    print(f'Audiobook saved as {output_file}')