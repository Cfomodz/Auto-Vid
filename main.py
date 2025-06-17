import os
import random
import json
import base64
import re
from dotenv import load_dotenv
from openai import OpenAI as OpenAIClient
from deepseek import DeepSeek as DeepSeekClient
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import moviepy.editor as mpy
from moviepy.video.fx import resize
from PIL import Image, ImageDraw, ImageFont
import requests
import numpy as np
from typing import List, Dict, Tuple

# Load environment variables
load_dotenv()

class VideoGenerator:
    def __init__(self, prompt):
        self.prompt = prompt
        self.openai = OpenAIClient(api_key=os.getenv('OPENAI_API_KEY'))
        self.deepseek = DeepSeekClient(api_key=os.getenv('DEEPSEEK_API_KEY'))
        self.elevenlabs = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        
        # Ensure directories exist
        os.makedirs("temp/images", exist_ok=True)
        os.makedirs("temp/sfx", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        # Font for captions
        self.font = "Arial.ttf"  # Use system font or provide path

    def research_topic(self):
        """Use DeepSeek to research topic and generate content plan"""
        response = self.deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You're a research assistant. Given a topic, identify key visual elements, narrative structure, and suggest sound effects."},
                {"role": "user", "content": f"Create a detailed content plan with 5-8 key scenes for a video about: {self.prompt}. For each scene, suggest a sound effect."}
            ]
        )
        return response.choices[0].message.content

    def generate_script(self, research):
        """Generate voiceover script using OpenAI with SFX markers"""
        response = self.openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You're a script writer. Create a concise voiceover script. Mark sound effects with [SFX: description]."},
                {"role": "user", "content": research}
            ]
        )
        return response.choices[0].message.content

    def extract_sfx_markers(self, script: str) -> List[Tuple[str, int]]:
        """Extract SFX markers and their positions in the script"""
        markers = []
        clean_script = script
        for match in re.finditer(r"\[SFX:(.*?)\]", script):
            markers.append((match.group(1).strip(), match.start()))
            clean_script = clean_script.replace(match.group(0), "")
        return clean_script, markers

    def generate_image_descriptions(self, script):
        """Generate image prompts from script"""
        response = self.openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Generate 5-8 detailed DALLE-3 image prompts for key moments in this script. Return as JSON: {'prompts': [list], 'sfx': [list of sound effect descriptions]}"},
                {"role": "user", "content": script}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def create_images(self, prompts):
        """Generate images using DALLE-3"""
        image_paths = []
        for i, prompt in enumerate(prompts):
            response = self.openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                n=1
            )
            img_url = response.data[0].url
            img_path = f"temp/images/image_{i}.png"
            self.download_image(img_url, img_path)
            image_paths.append(img_path)
        return image_paths

    def download_image(self, url, path):
        """Download image from URL"""
        response = requests.get(url)
        with open(path, 'wb') as f:
            f.write(response.content)
        # Ensure valid image
        Image.open(path).verify()

    def generate_voiceover(self, script: str):
        """Generate voiceover with letter-level timing using ElevenLabs"""
        response = self.elevenlabs.generate(
            text=script,
            voice="Adam",
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            return_detailed_timing=True
        )
        
        # Save audio
        audio_path = "temp/voiceover.mp3"
        save(response.audio, audio_path)
        
        # Process timing data
        timing_data = []
        for word in response.timing.words:
            for char in word.characters:
                timing_data.append({
                    "character": char.char,
                    "start": char.start,
                    "end": char.end,
                    "word_start": word.start,
                    "word_end": word.end,
                    "word": word.word
                })
        
        return audio_path, timing_data

    def generate_sound_effect(self, prompt: str, output_path: str):
        """Generate sound effect using ElevenLabs"""
        response = self.elevenlabs.sound_effects.generate(
            prompt=prompt,
            output_format="mp3_44100_128"
        )
        save(response.audio, output_path)
        return output_path

    def get_background_music(self):
        """Select random background music"""
        music_files = [f for f in os.listdir("music") if f.endswith(".wav")]
        return f"music/{random.choice(music_files)}" if music_files else None

    def create_ken_burns_effect(self, image_path: str, duration: float, zoom_factor: float = 1.2):
        """Create Ken Burns zoom effect for an image"""
        img = mpy.ImageClip(image_path)
        img = img.set_duration(duration)
        
        # Create zoom in/out effect
        def zoom_effect(t):
            progress = t / duration
            zoom = 1 + (zoom_factor - 1) * (1 - abs(2*progress - 1))
            return zoom
            
        return img.resize(zoom_effect)

    def create_word_caption(self, word: str, start: float, end: float, position: tuple, font_size: int = 60):
        """Create animated word caption with appearance effect"""
        # Create blank image with text
        img = Image.new('RGBA', (1920, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font, font_size)
        
        # Get text size
        text_width = draw.textlength(word, font=font)
        text_height = font_size
        
        # Create text image
        text_img = Image.new('RGBA', (int(text_width), int(text_height*1.5)), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text((0, 0), word, font=font, fill="white")
        
        # Convert to MoviePy clip
        clip = mpy.ImageClip(np.array(text_img)).set_start(start).set_end(end)
        clip = clip.set_position(('center', position[1]))
        
        # Add fade-in effect
        clip = clip.crossfadein(0.1)
        return clip

    def create_video(self, image_paths: List[str], voiceover_path: str, timing_data: List[Dict], 
                    sfx_data: List[Dict], music_path: str):
        """Compose final video with effects and captions"""
        # Load audio components
        voice_audio = mpy.AudioFileClip(voiceover_path)
        total_duration = voice_audio.duration
        
        # Create SFX clips
        sfx_clips = []
        for sfx in sfx_data:
            sfx_clip = mpy.AudioFileClip(sfx['path'])
            sfx_clip = sfx_clip.set_start(sfx['time'])
            sfx_clips.append(sfx_clip)
        
        # Add background music
        if music_path:
            bg_music = mpy.AudioFileClip(music_path).volumex(0.3)
            bg_music = bg_music.set_duration(total_duration)
            audio_clips = [voice_audio, bg_music] + sfx_clips
            final_audio = mpy.CompositeAudioClip(audio_clips)
        else:
            audio_clips = [voice_audio] + sfx_clips
            final_audio = mpy.CompositeAudioClip(audio_clips)
        
        # Create image clips with Ken Burns effect
        per_image_duration = total_duration / len(image_paths)
        image_clips = []
        for i, img_path in enumerate(image_paths):
            clip = self.create_ken_burns_effect(img_path, per_image_duration)
            clip = clip.set_start(i * per_image_duration)
            image_clips.append(clip)
        
        # Create caption clips
        caption_clips = []
        y_position = 0.8  # 80% from top
        current_word = None
        word_start = 0
        
        for i, char_data in enumerate(timing_data):
            # New word detection
            if current_word != char_data['word']:
                if current_word:
                    # Create clip for completed word
                    word_clip = self.create_word_caption(
                        current_word, 
                        word_start, 
                        char_data['start'], 
                        ('center', y_position)
                    )
                    caption_clips.append(word_clip)
                
                # Start new word
                current_word = char_data['word']
                word_start = char_data['start']
        
        # Add last word
        if current_word:
            word_clip = self.create_word_caption(
                current_word, 
                word_start, 
                timing_data[-1]['end'], 
                ('center', y_position)
            )
            caption_clips.append(word_clip)
        
        # Create video composite
        video = mpy.CompositeVideoClip(image_clips, size=(1920, 1080))
        video = video.set_audio(final_audio)
        video = video.set_duration(total_duration)
        
        # Add captions to video
        final = mpy.CompositeVideoClip([video] + caption_clips)
        final.write_videofile(
            "output/final_video.mp4", 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            threads=8,
            preset='slow',
            ffmpeg_params=['-crf', '18']
        )

    def execute(self):
        """Main execution pipeline"""
        print("🔍 Researching topic...")
        research = self.research_topic()
        
        print("📝 Generating script...")
        script = self.generate_script(research)
        print(f"Generated Script:\n{script}\n")
        
        # Extract SFX markers
        clean_script, sfx_markers = self.extract_sfx_markers(script)
        
        print("🖼️ Creating image prompts...")
        image_data = self.generate_image_descriptions(clean_script)
        image_prompts = image_data["prompts"]
        sfx_descriptions = image_data.get("sfx", [])
        
        print("🎨 Generating images...")
        image_paths = self.create_images(image_prompts)
        
        print("🔊 Generating voiceover with precise timing...")
        voiceover_path, timing_data = self.generate_voiceover(clean_script)
        
        print("🔉 Generating sound effects...")
        sfx_data = []
        for i, desc in enumerate(sfx_descriptions):
            sfx_path = f"temp/sfx/sfx_{i}.mp3"
            self.generate_sound_effect(desc, sfx_path)
            # Simple timing - place SFX at 25%, 50%, 75% of video
            sfx_time = (i + 1) * (len(image_paths) / (len(sfx_descriptions) + 1))
            sfx_data.append({"path": sfx_path, "time": sfx_time})
        
        print("🎵 Selecting background music...")
        music_path = self.get_background_music()
        
        print("🎬 Composing video with advanced effects...")
        self.create_video(image_paths, voiceover_path, timing_data, sfx_data, music_path)
        
        print("✅ Video created at output/final_video.mp4")

if __name__ == "__main__":
    topic = input("Enter video topic: ")
    generator = VideoGenerator(topic)
    generator.execute()
