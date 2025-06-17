# 🎥 AI Video Production Toolkit 🚀

Automated video creation with perfect audio-visual synchronization, dynamic captions, and immersive sound effects
## ✨ Key Features
### ⏱️ Precise Timing Integration

    Uses ElevenLabs' return_detailed_timing=True for letter-level synchronization 🔤

    Processes character-by-character timing data for perfect caption sync

    Implements word-by-word animated captions with smooth fade effects 🌊

### 🔊 Sound Effects System

    Uses ElevenLabs' sound_effects.generate endpoint

    Implements SFX markers in scripts ([SFX: thunder]) ⚡

    Automatic SFX generation based on scene descriptions

    Multi-track audio mixing (voice + music + SFX) 🎚️

### 📜 Enhanced Captions

    Dynamic word-by-word text animations

    Professional font rendering with PIL (Pillow) ✒️

    Smooth fade-in/out transitions

    Frame-perfect synchronization with voice audio 🎯

### 🎬 Optimized Video Production

    Improved Ken Burns effect with smooth zoom curves 🔍

    Multi-threaded rendering with quality settings ⚡

    Efficient audio mixing pipeline

    Robust error handling and validation ✅

### 🤖 AI Coordination

    DeepSeek for SFX-aware research 🔍

    GPT-4 for SFX-marked script generation ✍️

    DALL·E 3 for high-quality images 🖼️

    ElevenLabs for voice & sound effects 🔊

## 🛠️ Setup Instructions
### 1. Install Requirements
```bash
pip install openai deepseek-cfg elevenlabs moviepy pillow python-dotenv requests
```

### 2. Configure Environment

Create .env file with your API keys:
```ini
OPENAI_API_KEY=your_openai_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

3. Folder Structure

```markdown
project/
├── main.py
├── .env
├── music/               # Background tracks
│   ├── intense.mp3
│   └── ambient.wav
├── temp/                # Auto-generated assets
│   ├── images/
│   ├── sfx/
│   └── voiceover.mp3
└── output/              # Final renders
```
## 🚀 Usage

Run the script and enter your topic:
```bash
python main.py
> Enter video topic: "Quantum Computing Breakthroughs"
```
### The system will automatically:

    📝 Generate SFX-marked script with GPT-4

    🎨 Create visuals with DALL·E 3

    🔊 Generate voiceover & sound effects with ElevenLabs

    ⚙️ Render video with synchronized captions

    💾 Save final video in /output

## 🎯 Example Output

Dynamic captions with word-level animations + layered audio tracks

## 📌 Requirements
```
  FFmpeg installed system-wide

  High-quality music tracks in /music folder
```
Made with ❤️ for the community
