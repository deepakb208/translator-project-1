import os
import shutil
from gtts import gTTS
import audioread
from docx import Document
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *

# Initialize Google Text-to-Speech client
def synthesize_speech(text, output_file):
    tts = gTTS(text=text, lang='en', tld='co.in', slow=False)
    tts.save(output_file)
    print(f'Audio content written to file {output_file}')

# Split text into smaller chunks for TTS processing
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

# Generate image from text
def generate_image(text, output_path):
    img = Image.new('RGB', (1920, 1080), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    text = "\n".join(text.split("\n"))
    d.text((50, 50), text, fill=(0, 0, 0), font=font)
    img.save(output_path)

# Get the duration of an audio file in seconds
def get_audio_duration(file_path):
    with audioread.audio_open(file_path) as f:
        return f.duration

# Convert text to speech and create video with synced text images
def text_to_speech_to_video(text, verses, chapter_number, output_dir):
    text_chunks = split_text(text)
    
    temp_audio_dir = os.path.join(output_dir, f"temp_audio_chunks_chapter_{chapter_number}")
    temp_image_dir = os.path.join(output_dir, f"temp_image_chunks_chapter_{chapter_number}")
    os.makedirs(temp_audio_dir, exist_ok=True)
    os.makedirs(temp_image_dir, exist_ok=True)
    
    audio_files = []
    image_files = []
    total_duration = 0
    
    for i, chunk in enumerate(text_chunks):
        chunk_audio_file = os.path.join(temp_audio_dir, f"chunk_{i}.mp3")
        synthesize_speech(chunk, chunk_audio_file)
        audio_files.append(chunk_audio_file)
        
        duration = get_audio_duration(chunk_audio_file)
        
        verse_image_file = os.path.join(temp_image_dir, f"verse_{i}.png")
        generate_image(verses[i % len(verses)], verse_image_file)
        image_files.append((verse_image_file, duration))
        total_duration += duration
    
    # Create video using moviepy
    video_clips = []
    for i, (image_file, duration) in enumerate(image_files):
        img_clip = ImageClip(image_file).set_duration(duration)
        audio_clip = AudioFileClip(audio_files[i]).subclip(0, duration)
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
    verses = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            verses.append(paragraph.text.strip())
    
    chapters = text.split('Chapter ')
    for chapter in chapters[1:]:
        chapter_number = chapter.split('\n')[0].strip()
        chapter_text = 'Chapter ' + chapter
        print(f'Processing Chapter {chapter_number}')
        text_to_speech_to_video(chapter_text, verses, chapter_number, output_dir)



if __name__ == "__main__":
    text_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final.txt'
    docx_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final_video_text.docx'
    output_dir = 'output_videos'
    os.makedirs(output_dir, exist_ok=True)
    process_text_file(text_file, docx_file, output_dir)
    print(f'Videos saved in {output_dir}')