#!/usr/bin/env python

import os
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import whisper
import tempfile
import time
from pathlib import Path
from anthropic import Anthropic

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
    num_pixels = 100
    ORDER = neopixel.GRB

    pixels = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=0.9, pixel_order=ORDER
    )
except (ImportError, NotImplementedError, RuntimeError) as e:
    LED_AVAILABLE = False
    pixels = None
    print(f"LED hardware not available: {e}")
    print("Running in terminal-only mode.\n")

# Character to LED position mapping
char_to_pixel_map = {
    'R': 11, 'S': 15, 'T': 18, 'U': 21, 'V': 24, 'W': 27, 'X': 31, 'Y': 33, 'Z': 36,
    'Q': 44, 'P': 47, 'O': 49, 'N': 50, 'M': 53, 'L': 57, 'K': 59, 'J': 62, 'I': 65,
    'A': 73, 'B': 76, 'C': 80, 'D': 83, 'E': 87, 'F': 90, 'G': 92, 'H': 95
}

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
RECORDING_DURATION = 5  # seconds

def play_pixel(i, color, duration):
    """Light up a specific LED with a color for a duration, then turn it off."""
    pixels[i] = color
    time.sleep(duration)
    pixels[i] = (0, 0, 0)

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

        if ch not in char_to_pixel_map:
            continue

        time.sleep(seconds_between_character)
        play_pixel(
            char_to_pixel_map[ch],
            colors[ich % len(colors)],
            seconds_per_character,
        )

    pixels.fill((0, 0, 0))

def record_audio(duration=RECORDING_DURATION):
    """Record audio from the microphone."""
    print(f"🎤 Recording for {duration} seconds... SPEAK NOW!")

    audio_data = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=np.int16
    )

    sd.wait()
    print("✓ Recording finished!")

    return audio_data

def transcribe_audio(audio_data, model):
    """Transcribe audio using Whisper."""
    print("🔄 Transcribing...")

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
        "Keep responses concise (under 50 characters when possible) and use only letters and spaces, "
        "as these will be flashed one character at a time on individual LEDs. "
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
    print("=" * 60)
    print("🎙️  Will Byers Voice Chat")
    print("=" * 60)
    print("Press ENTER to start recording, speak your message,")
    print("and Will will respond through the lights!")
    if LED_AVAILABLE:
        print("Responses will be flashed on the LEDs.")
    else:
        print("Running in terminal-only mode (LED hardware not connected).")
    print("Type 'quit' or 'exit' then press ENTER to stop.")
    print("=" * 60)

    # Load Whisper model once at startup
    print("\n📥 Loading Whisper model (this may take a moment)...")
    model = whisper.load_model("base")
    print("✓ Model loaded!\n")

    # Clear all LEDs at start if available
    if LED_AVAILABLE and pixels is not None:
        pixels.fill((0, 0, 0))

    while True:
        try:
            # Wait for user to press Enter
            user_input = input("\nPress ENTER to record (or type 'quit' to exit): ").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                if LED_AVAILABLE and pixels is not None:
                    pixels.fill((0, 0, 0))
                break

            # Record audio
            audio = record_audio()

            # Transcribe
            transcription = transcribe_audio(audio, model)

            if not transcription:
                print("❌ No speech detected. Please try again.")
                continue

            print(f"\n📝 You said: \"{transcription}\"")

            # Get Claude's response
            print("💭 Getting response from Will...")
            response = get_claude_response(transcription)
            print(f"\n💡 Will says: {response}")

            # Flash the response on LEDs
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
