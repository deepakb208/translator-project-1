import os
import shutil
from gtts import gTTS
import audioread
from docx import Document
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from google.cloud import texttospeech

# Initialize Google Text-to-Speech client
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
    print(f'Audio content written to file {output_file}')

# Split text into smaller chunks for TTS processing
def split_text(text):
    paragraphs = text.split('\n')
    verses = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
    return verses

def split_video_text(video_text):
    video_verses = []
    verses = video_text.split('Verse ')
    chapter_text = verses[0].strip()
    if chapter_text.startswith('Chapter'):
        video_verses.append(chapter_text)
    for verse in verses[1:]:
        video_verses.append('Verse ' + verse.strip())
    return video_verses

def generate_image(text, output_path):
    # Define image size and create a blank image
    img = Image.new('RGB', (1920, 1080), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        # Load a font that supports Sanskrit text
        font = ImageFont.truetype("NotoSans-Regular.ttf", 40 * 5)  # 5x the font size
    except IOError:
        font = ImageFont.load_default()

    # Split the text into lines
    lines = text.split("\n")

    # Calculate the position to center the text
    current_h = 50
    padding = 10
    for i, line in enumerate(lines):
        # Calculate the bounding box of the text to be drawn
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # Center the text
        position = ((img.width - w) / 2, current_h)
        # Draw the text
        draw.text(position, line, fill=(0, 0, 0), font=font)
        # Update the height position
        current_h += h + padding
        # Add extra gap after specific lines
        if (i + 1) % 2 == 0:
            current_h += h  # Add gap equal to the height of the text

    # Save the image
    img.save(output_path)
    print(f'Image content written to file {output_path}')
    
# Get the duration of an audio file in seconds
def get_audio_duration(file_path):
    with audioread.audio_open(file_path) as f:
        return f.duration

# Convert text to speech and create video with synced text images
def text_to_speech_to_video(text, video_text, chapter_number, output_dir):
    verses = split_text(text)
    # print('Verses length: ' + str(len(verses)))
    video_verses = split_video_text(video_text)
    # print('Video verses length: ' + str(len(video_verses)))
    
    temp_audio_dir = os.path.join(output_dir, f"temp_audio_chunks_chapter_{chapter_number}")
    temp_image_dir = os.path.join(output_dir, f"temp_image_chunks_chapter_{chapter_number}")
    os.makedirs(temp_audio_dir, exist_ok=True)
    os.makedirs(temp_image_dir, exist_ok=True)
    
    audio_files = []
    image_files = []
    total_duration = 0
    
    for i, verse in enumerate(verses):
        # print('Verse: ' + verse)
        verse_audio_file = os.path.join(temp_audio_dir, f"verse_{i}.mp3")
        synthesize_speech(verse, verse_audio_file)
        audio_files.append(verse_audio_file)
        
        duration = get_audio_duration(verse_audio_file)
        
        verse_image_file = os.path.join(temp_image_dir, f"verse_{i}.png")
        generate_image(video_verses[i], verse_image_file)
        image_files.append((verse_image_file, duration))
        total_duration += duration
    
    # Create video using moviepy
    video_clips = []
    for i, (image_file, duration) in enumerate(image_files):
        img_clip = ImageClip(image_file).set_duration(duration)
        audio_clip = AudioFileClip(audio_files[i])
        audio_duration = audio_clip.duration

        # Ensure the audio and video durations match
        if duration > audio_duration:
            img_clip = img_clip.set_duration(audio_duration)
        else:
            audio_clip = audio_clip.subclip(0, duration)

        img_clip = img_clip.set_audio(audio_clip)
        video_clips.append(img_clip)
    
    final_video = concatenate_videoclips(video_clips)
    
    chapter_video_file = os.path.join(output_dir, f"tripura_rahasya_chapter_{chapter_number}.mp4")
    final_video.write_videofile(chapter_video_file, fps=24, audio_codec='aac')
    
    # Clean up temporary files and directories
    shutil.rmtree(temp_audio_dir)
    shutil.rmtree(temp_image_dir)

def process_text_file(text_file, docx_file, output_dir):
    with open(text_file, 'r') as file:
        text = file.read()
    
    document = Document(docx_file)
    video_verses = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            video_verses.append(paragraph.text.strip())
    
    document = Document(docx_file)
    video_text = '\n'.join([para.text for para in document.paragraphs])
    chapters = text.split('Chapter ')
    video_chapters = video_text.split('Chapter ')
    chapters_list = [chapters[1]]
    for i, chapter in enumerate(chapters_list):
        chapter_number = chapter.split('\n')[0].strip()
        chapter_text = 'Chapter ' + chapter
        video_chapter_text = 'Chapter ' + video_chapters[i+1]
        print(f'Processing Chapter {chapter_number}')
        text_to_speech_to_video(chapter_text, video_chapter_text, chapter_number, output_dir)

if __name__ == "__main__":
    text_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final.txt'
    docx_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final_video_text.docx'
    output_dir = 'output_videos'
    os.makedirs(output_dir, exist_ok=True)
    process_text_file(text_file, docx_file, output_dir)
    print(f'Videos saved in {output_dir}')