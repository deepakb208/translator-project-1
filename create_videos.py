import os
import shutil
from gtts import gTTS
import audioread
from docx import Document
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import *
from google.cloud import texttospeech

# Initialize Google Text-to-Speech client
def synthesize_speech(text, output_file, voice_name="en-IN-Standard-B", speaking_rate=0.7):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-IN",
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
    # verses = re.split(r'(Verse \d+|End)', video_text)
    chapter_text = verses[0].strip()
    if chapter_text.startswith('CHAPTER'):
        video_verses.append(chapter_text)
    for i, verse in enumerate(verses[1:]):
        if i == len(verses[1:]) - 1:
            parts = verse.split('End', 1)
            video_verses.append('Verse ' + parts[0].strip())
            video_verses.append(parts[1].strip())
        else:
            video_verses.append('Verse ' + verse.strip())
    return video_verses

def create_spiritual_background(width, height):
    # Create a new image with a gradient background
    base = Image.new('RGB', (width, height), color=(255, 255, 255))
    top_color = (250, 232, 212)  # Light cream color
    bottom_color = (191, 142, 113)  # Soft brown color

    for y in range(height):
        # Calculate the color at each y coordinate to create a gradient
        r = top_color[0] + (bottom_color[0] - top_color[0]) * y // height
        g = top_color[1] + (bottom_color[1] - top_color[1]) * y // height
        b = top_color[2] + (bottom_color[2] - top_color[2]) * y // height
        for x in range(width):
            base.putpixel((x, y), (r, g, b))

    # Optionally add a blur to soften the gradient
    base = base.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Draw the border
    draw = ImageDraw.Draw(base)
    border_color = (139, 69, 19)  # Saddle brown color
    border_width = 20

    for i in range(border_width):
        draw.rectangle(
            [i, i, width - i - 1, height - i - 1],
            outline=border_color
        )
    
    return base

def determine_font(line, bold=False, scale=1):
    try:
        # Load fonts
        sanskrit_font = ImageFont.truetype("fonts/NotoSansDevanagari-Regular.ttf", 40*scale)
        english_font = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 40*scale)
        transliteration_font = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 40*scale)  # Using Arial Unicode MS
        sanskrit_bold_font = ImageFont.truetype("fonts/NotoSansDevanagari-Bold.ttf", 40*scale)
        english_bold_font = ImageFont.truetype("fonts/NotoSans-Bold.ttf", 40*scale)
        transliteration_bold_font = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 40*scale)
    except IOError:
        sanskrit_font = ImageFont.load_default()
        english_font = ImageFont.load_default()
        transliteration_font = ImageFont.load_default()
        sanskrit_bold_font = ImageFont.load_default()
        english_bold_font = ImageFont.load_default()
        transliteration_bold_font = ImageFont.load_default()
    
    # Check if the line contains Devanagari script
    return_font = english_bold_font
    if any('\u0900' <= c <= '\u097F' for c in line):
        return_font = sanskrit_bold_font
    # Check if the line contains Latin characters used in transliteration
    if any(c in 'āĀăĂąĄćĆčČďĎđĐèÈêÊëËġĠĝĜğĞģĜįĮĵĴķĶĺĽļĻŀŁńŃňŇñÑòÒóÓôÔõÕöÖřŘśŚšŠţŢťŤùÙúÚûÛüÜýÝÿŸžŽḥḫḭḯḱḳḷḹḻḽṁṃṅṇṇṉṅḍḌḍṭṭḹḷḿṅṡṧṭṭʃʰʱʲʳʴʵʶʷʸ' for c in line):
        return_font = transliteration_bold_font if bold else transliteration_font
    
    return return_font

def text_width(draw, text, font):
        return draw.textbbox((0, 0), text, font=font)[2] - draw.textbbox((0, 0), text, font=font)[0]

def generate_image(text, output_path):
    # Define image size and create a blank image with spiritual background
    width, height = 1920, 1080
    # img = create_spiritual_background(width, height)
    img = Image.open('images/border-image-1.webp')
    draw = ImageDraw.Draw(img)
    
    # Define left and right margins (in pixels)
    left_margin = 200
    right_margin = 200

    # Split the text into lines
    lines = text.split("\n")

    # Split the last line into two parts at the nearest space if necessary
    if lines:
        last_line = lines[-1]
        if len(last_line) > 40:  # Adjust the length condition as needed
            words = last_line.split()
            mid_point = len(words) // 2
            lines[-1] = ' '.join(words[:mid_point]) + '\n' + ' '.join(words[mid_point:])
            lines = lines[:-1] + lines[-1].split('\n')  # Add the split lines back to the list
            
    # Adjust lines to fit within margins
    adjusted_lines = []
    for line in lines:
        font = determine_font(line)
        words = line.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if text_width(draw, test_line, font) > (img.width - left_margin - right_margin):
                if current_line:
                    adjusted_lines.append(current_line.strip())
                current_line = word
            else:
                current_line = test_line
        if current_line:
            adjusted_lines.append(current_line.strip())

    lines = adjusted_lines

    # Calculate the total height of the text to be drawn, including padding
    padding = 10
    total_height = sum(
        draw.textbbox((0, 0), line, font=determine_font(line, True, 1.25))[3] - draw.textbbox((0, 0), line, font=determine_font(line, True, 1.25))[1]
        for line in lines
    ) + padding * (len(lines) - 1)    
    # Move the text a little up by reducing current_h value
    current_h = (img.height - total_height) // 2 - 75

    for i, line in enumerate(lines):
        # Determine font based on content
        if i == 0:
            font = determine_font(line, True)
        else:
            font = determine_font(line)
        # Calculate the bounding box of the text to be drawn
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Center the text horizontally within the margins
        position = (left_margin + (img.width - left_margin - right_margin - w) / 2, current_h)
        # Draw the text
        draw.text(position, line, fill=(0, 0, 0), font=font)
        # Update the height position
        current_h += h + padding

        # Add extra gap after the first, third, and fifth lines
        if i == 0 or i == 2 or i == 4:
            current_h += h

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
    video_verses = split_video_text(video_text)
    # count = 5
    
    temp_audio_dir = os.path.join(output_dir, f"temp_audio_chunks_chapter_{chapter_number}")
    temp_image_dir = os.path.join(output_dir, f"temp_image_chunks_chapter_{chapter_number}")
    os.makedirs(temp_audio_dir, exist_ok=True)
    os.makedirs(temp_image_dir, exist_ok=True)
    
    audio_files = []
    image_files = []
    total_duration = 0
    
    for i, verse in enumerate(verses):
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
    
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    chapter_video_file = os.path.join(output_dir, f"tripura_rahasya_chapter_{chapter_number}.mp4")
    final_video.write_videofile(chapter_video_file, fps=24, codec='libx264', audio_codec='aac')
    
    # Clean up temporary files and directories
    shutil.rmtree(temp_audio_dir)
    shutil.rmtree(temp_image_dir)

def process_text_file(text_file, docx_file, output_dir):
    with open(text_file, 'r') as file:
        text = file.read()
    
    document = Document(docx_file)
    video_text = '\n'.join([para.text for para in document.paragraphs])
    chapters = text.split('CHAPTER ')
    video_chapters = video_text.split('CHAPTER ')
    chapters_list = [chapters[1]]
    for i, chapter in enumerate(chapters_list):
        chapter_number = chapter.split('\n')[0].strip()
        chapter_text = 'CHAPTER ' + chapter
        video_chapter_text = 'CHAPTER ' + video_chapters[i+1]
        print(f'Processing Chapter {chapter_number}')
        text_to_speech_to_video(chapter_text, video_chapter_text, chapter_number, output_dir)

if __name__ == "__main__":
    text_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final.txt'
    docx_file = 'input/tripura_rahasya_english_final/tripura_rahasya_english_final_video_text.docx'
    output_dir = 'output_videos'
    os.makedirs(output_dir, exist_ok=True)
    process_text_file(text_file, docx_file, output_dir)
    print(f'Videos saved in {output_dir}')