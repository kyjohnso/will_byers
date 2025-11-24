#!/usr/bin/env python

import os
import sys
import argparse
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import whisper
import tempfile
import time
import threading
import random
import requests
from pathlib import Path
from anthropic import Anthropic
from .led_config import load_led_mapping_with_fallback

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file in the project root."""
    search_paths = [
        Path.cwd() / '.env',
        Path.cwd().parent / '.env',
        Path(__file__).parent.parent / '.env',
    ]

    for env_path in search_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
            return

load_env_file()

# Try to import LED libraries
try:
    import board
    import neopixel
    LED_AVAILABLE = True

    pixel_pin = board.D18
    num_pixels = 150
    ORDER = neopixel.GRB

    pixels = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=0.9, pixel_order=ORDER
    )
except (ImportError, NotImplementedError, RuntimeError) as e:
    LED_AVAILABLE = False
    pixels = None
    print(f"LED hardware not available: {e}")
    print("Running in terminal-only mode.\n")

# Load character to LED position mapping from JSON file
char_to_pixel_map = load_led_mapping_with_fallback()

# Timing configuration
seconds_per_character = 0.9
seconds_between_character = 0.2

# Color configuration
colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (128, 128, 128), # Gray
]

# Audio recording configuration
SAMPLE_RATE = 48000  # 48kHz (USB mic requirement, Whisper will resample internally)
CHANNELS = 1

def play_pixel(i, color, duration):
    """Light up a specific LED with a color for a duration, then turn it off."""
    pixels[i] = color
    time.sleep(duration)
    pixels[i] = (0, 0, 0)

def flash_all_lights_multicolor(times=8, duration=0.15):
    """Flash random lights in random colors - dramatic effect for '!'."""
    if not LED_AVAILABLE or pixels is None:
        print("(Dramatic light flashing skipped - hardware not available)")
        return

    # Fixed duration between 2 and 4 seconds for dramatic effect
    total_duration = random.uniform(2.0, 4.0)
    print(f"⚠️  DRAMATIC LIGHT FLASH! ({total_duration:.1f}s) ⚠️")
    
    flash_colors = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 255, 0),    # Yellow
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 128, 0),    # Orange
        (255, 255, 255),  # White
    ]

    # Track actual time to ensure we don't exceed total_duration
    start_time = time.time()
    flash_duration = 0.08  # Each flash lasts 0.08 seconds
    
    # Number of random lights to change per flash (about 20-40% of total)
    lights_per_flash = random.randint(num_pixels // 5, num_pixels // 2)
    
    while (time.time() - start_time) < total_duration:
        # Turn off all lights first
        pixels.fill((0, 0, 0))
        
        # Pick random lights and assign random colors
        random_indices = random.sample(range(num_pixels), lights_per_flash)
        for pixel_idx in random_indices:
            pixels[pixel_idx] = random.choice(flash_colors)
        
        time.sleep(flash_duration)

    pixels.fill((0, 0, 0))  # All off
    time.sleep(0.3)  # Brief pause

def flash_message(message):
    """Flash a message on the LEDs character by character."""
    if not LED_AVAILABLE or pixels is None:
        print("(LED flashing skipped - hardware not available)")
        return

    pixels.fill((0, 0, 0))

    for ich, ch in enumerate(message.upper()):
        if ch == " ":
            pixels.fill((0, 0, 0))
            time.sleep(3 * seconds_between_character)
            continue

        # Special dramatic effect for exclamation point!
        if ch == "!":
            flash_all_lights_multicolor(times=8, duration=0.15)
            continue

        if ch not in char_to_pixel_map:
            continue

        time.sleep(seconds_between_character)
        play_pixel(
            char_to_pixel_map[ch],
            colors[ich % len(colors)],
            seconds_per_character,
        )

    pixels.fill((0, 0, 0))

def record_audio_until_enter():
    """Record audio until user presses Enter."""
    print("\n🎤 Recording... Press ENTER to stop!")

    # Storage for recorded chunks
    recording = []

    def audio_callback(indata, frames, time, status):
        """This is called for each audio block."""
        if status:
            print(status)
        recording.append(indata.copy())

    # Start recording in a stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=np.int16,
        callback=audio_callback
    )

    with stream:
        # Wait for user to press Enter
        input()

    print("✓ Recording stopped!")

    # Concatenate all chunks into one array
    if recording:
        audio_data = np.concatenate(recording, axis=0)
        return audio_data
    else:
        return np.array([], dtype=np.int16)

def transcribe_audio_local(audio_data, model):
    """Transcribe audio using local Whisper model."""
    print("🔄 Transcribing locally...")

    # Save to temporary file (Whisper needs a file)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        wavfile.write(temp_path, SAMPLE_RATE, audio_data)

    try:
        result = model.transcribe(temp_path, language="en")
        transcription = result["text"].strip()
        return transcription
    finally:
        # Clean up temp file
        os.unlink(temp_path)


def transcribe_audio_remote(audio_data, server_url):
    """Transcribe audio using remote Whisper server."""
    print(f"🔄 Transcribing via remote server ({server_url})...")

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        wavfile.write(temp_path, SAMPLE_RATE, audio_data)

    try:
        # Send audio to remote server
        with open(temp_path, 'rb') as audio_file:
            files = {'audio': ('audio.wav', audio_file, 'audio/wav')}
            data = {'language': 'en'}
            
            response = requests.post(
                f"{server_url}/transcribe",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get('text', '').strip()
                return transcription
            else:
                raise Exception(f"Server returned error: {response.status_code} - {response.text}")
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)

def get_claude_response(user_message):
    """Send a message to Claude and get a response."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found.\n"
            "Please set it using one of these methods:\n"
            "1. Create a .env file in the project root with: ANTHROPIC_API_KEY=your-api-key-here\n"
            "2. Export it: export ANTHROPIC_API_KEY='your-api-key-here'\n"
            "3. Run with sudo -E: sudo -E will-byers-voice-chat"
        )

    client = Anthropic(api_key=api_key)

    system_prompt = (
        "You are Will Byers from the Stranger Things show, trapped in the Upside Down. "
        "You are communicating through a string of LED lights (like the Christmas lights scene). "
        "Keep responses concise (under 50 characters when possible) and use only letters, spaces, and exclamation points. "
        "When you want to express urgency, danger, or strong emotion, you can use an exclamation point (!) "
        "which will cause ALL the lights to flash rapidly in different colors as a dramatic warning. "
        "Use exclamation points sparingly for maximum impact - for danger, fear, or urgent warnings. "
        "Stay in character as Will - you're scared, trying to communicate with your mom and friends, "
        "but also brave and resourceful."
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    return message.content[0].text

def main():
    """Main loop: record audio, transcribe, get Claude response, flash on LEDs."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Will Byers Voice Chat - Communicate through the lights!'
    )
    parser.add_argument(
        '--remote-whisper',
        type=str,
        default=None,
        metavar='URL',
        help='URL of remote Whisper server (e.g., http://192.168.1.100:5000)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎙️  Will Byers Voice Chat")
    print("=" * 60)
    print("Press ENTER to start recording.")
    print("Speak your message, then press ENTER to stop.")
    print("Will will respond through the lights!")
    if LED_AVAILABLE:
        print("Responses will be flashed on the LEDs.")
    else:
        print("Running in terminal-only mode (LED hardware not connected).")
    print("Type 'quit' or 'exit' then press ENTER to stop.")
    print("=" * 60)

    # Setup transcription method
    model = None
    remote_server = args.remote_whisper
    
    if remote_server:
        print(f"\n🌐 Using remote Whisper server: {remote_server}")
        # Test connection to remote server
        try:
            response = requests.get(f"{remote_server}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✓ Connected! Server model: {health.get('model', 'unknown')}, "
                      f"device: {health.get('device', 'unknown')}\n")
            else:
                print(f"⚠️  Warning: Server health check returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to remote server: {e}")
            print("Will attempt to use it anyway...\n")
    else:
        # Load Whisper model locally
        print("\n📥 Loading local Whisper model (this may take a moment)...")
        model = whisper.load_model("base")
        print("✓ Model loaded!\n")

    # Clear all LEDs at start if available
    if LED_AVAILABLE and pixels is not None:
        pixels.fill((0, 0, 0))

    while True:
        try:
            # Wait for user to press Enter
            user_input = input("\nPress ENTER to start recording (or type 'quit' to exit): ").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                if LED_AVAILABLE and pixels is not None:
                    pixels.fill((0, 0, 0))
                break

            # Record audio
            audio = record_audio_until_enter()

            # Transcribe using appropriate method
            if remote_server:
                transcription = transcribe_audio_remote(audio, remote_server)
            else:
                transcription = transcribe_audio_local(audio, model)

            if not transcription:
                print("❌ No speech detected. Please try again.")
                continue

            print(f"\n📝 You said: \"{transcription}\"")

            # Get Claude's response
            print("💭 Getting response from Will...")
            response = get_claude_response(transcription)
            print(f"\n💡 Will says: {response}")

            # Flash the response on LEDs (exclamation points will trigger dramatic effect)
            if LED_AVAILABLE:
                print("\n✨ Flashing response on LEDs...")
            flash_message(response)
            print("✓ Done!")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            if LED_AVAILABLE and pixels is not None:
                pixels.fill((0, 0, 0))
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()
