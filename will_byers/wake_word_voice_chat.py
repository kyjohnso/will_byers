#!/usr/bin/env python

import os
import sys
import argparse
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import scipy.signal as signal
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

# Try to import Vosk for wake word detection
try:
    from vosk import Model, KaldiRecognizer
    import json as json_module
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: vosk not installed. Wake word detection disabled.")
    print("Install with: pip install vosk")

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
RECORDING_DURATION = 5  # seconds to record after wake word

def play_pixel(i, color, duration):
    """Light up a specific LED with a color for a duration, then turn it off."""
    pixels[i] = color
    time.sleep(duration)
    pixels[i] = (0, 0, 0)

def quick_flash_acknowledgment():
    """Quick flash of all lights to acknowledge wake word detection."""
    if not LED_AVAILABLE or pixels is None:
        print("💡 (Wake word acknowledged - LED flash skipped)")
        return
    
    # Flash all lights white briefly
    pixels.fill((255, 255, 255))
    time.sleep(0.1)
    pixels.fill((0, 0, 0))
    time.sleep(0.05)
    pixels.fill((255, 255, 255))
    time.sleep(0.1)
    pixels.fill((0, 0, 0))

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

def record_audio_fixed_duration(duration=RECORDING_DURATION):
    """Record audio for a fixed duration."""
    print(f"🎤 Recording for {duration} seconds...")

    # Calculate number of samples
    num_samples = int(SAMPLE_RATE * duration)
    
    # Record audio
    audio_data = sd.rec(
        num_samples,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=np.int16
    )
    
    # Wait for recording to complete
    sd.wait()
    
    print("✓ Recording complete!")
    
    return audio_data

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
            "3. Run with sudo -E: sudo -E will-byers-wake-word-chat"
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

def download_vosk_model():
    """Download Vosk model if not present."""
    model_path = Path.home() / ".cache" / "vosk" / "vosk-model-small-en-us-0.15"
    
    if model_path.exists():
        return str(model_path)
    
    print("📥 Downloading Vosk speech recognition model...")
    print("   (This is a one-time download, ~40MB)")
    
    try:
        import urllib.request
        import zipfile
        
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download small English model
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = model_path.parent / "model.zip"
        
        print(f"   Downloading from: {model_url}")
        urllib.request.urlretrieve(model_url, zip_path)
        
        print("   Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_path.parent)
        
        zip_path.unlink()
        
        print("✓ Model downloaded successfully!")
        return str(model_path)
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        print(f"\n💡 Manual download:")
        print(f"   1. Download from: https://alphacephei.com/vosk/models")
        print(f"   2. Extract to: {model_path}")
        return None

def listen_for_wake_word(wake_word="will", sensitivity=1e-20):
    """
    Listen continuously for the wake word using Vosk.
    Returns True when wake word is detected.
    
    Vosk is a modern, offline speech recognition toolkit that works great
    on Raspberry Pi and doesn't require complex model setup.
    """
    if not VOSK_AVAILABLE:
        print("❌ Vosk not available. Cannot listen for wake word.")
        print("   Install with: pip install vosk")
        return False
    
    # Download model if needed
    model_path = download_vosk_model()
    if not model_path:
        return False
    
    try:
        print(f"👂 Listening for wake word: '{wake_word}'...")
        print("   (Speak clearly and wait for acknowledgment)")
        
        # Load Vosk model
        model = Model(model_path)
        
        # Vosk works best with 16kHz audio
        CAPTURE_RATE = 48000
        TARGET_RATE = 16000
        
        # Create recognizer
        recognizer = KaldiRecognizer(model, TARGET_RATE)
        recognizer.SetWords(True)
        
        # Use a queue to handle audio in callback
        import queue
        audio_queue = queue.Queue()
        
        def audio_callback(indata, frames, time_info, status):
            """Called for each audio block."""
            # Put audio data in queue for processing
            audio_queue.put(indata.copy())
        
        # Start audio stream at 48kHz with callback
        stream = sd.InputStream(
            samplerate=CAPTURE_RATE,
            channels=1,
            dtype=np.int16,
            callback=audio_callback,
            blocksize=4800  # 100ms at 48kHz
        )
        
        try:
            with stream:
                while True:
                    try:
                        # Get audio from queue (with timeout to allow checking for Ctrl+C)
                        audio_chunk = audio_queue.get(timeout=0.1)
                        
                        # Resample from 48kHz to 16kHz for Vosk
                        audio_16k = signal.resample(
                            audio_chunk.flatten(),
                            int(len(audio_chunk) * TARGET_RATE / CAPTURE_RATE)
                        )
                        
                        # Convert to int16 bytes
                        audio_16k = audio_16k.astype(np.int16).tobytes()
                        
                        # Process with Vosk
                        if recognizer.AcceptWaveform(audio_16k):
                            result = json_module.loads(recognizer.Result())
                            text = result.get('text', '').lower()
                            
                            # Print what was heard for debugging
                            if text.strip():
                                print(f"   Heard: '{text}'")
                            
                            if wake_word.lower() in text:
                                print(f"\n✓ Wake word '{wake_word}' detected!")
                                return True
                        else:
                            # Check partial results too for faster response
                            partial = json_module.loads(recognizer.PartialResult())
                            text = partial.get('partial', '').lower()
                            
                            if text.strip() and wake_word.lower() in text:
                                print(f"\n✓ Wake word '{wake_word}' detected!")
                                print(f"   (Heard: '{text}')")
                                return True
                                
                    except queue.Empty:
                        continue
                        
        except KeyboardInterrupt:
            print("\n   Cancelled by user")
            return False
                
    except KeyboardInterrupt:
        return False
    except Exception as e:
        print(f"❌ Error in wake word detection: {e}")
        print(f"\nTroubleshooting:")
        print(f"   1. Make sure you have: pip install vosk")
        print(f"   2. Check model downloaded to: {model_path}")
        return False

def main():
    """Main loop: listen for wake word, record audio, transcribe, get Claude response, flash on LEDs."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Will Byers Wake Word Voice Chat - Say "will" to start!'
    )
    parser.add_argument(
        '--remote-whisper',
        type=str,
        default=None,
        metavar='URL',
        help='URL of remote Whisper server (e.g., http://192.168.1.100:5000)'
    )
    parser.add_argument(
        '--wake-word',
        type=str,
        default='will',
        help='Wake word to listen for (default: will)'
    )
    parser.add_argument(
        '--sensitivity',
        type=float,
        default=1e-20,
        help='Wake word detection sensitivity (lower = more sensitive, default: 1e-20)'
    )
    parser.add_argument(
        '--record-duration',
        type=int,
        default=5,
        help='Seconds to record after wake word (default: 5)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎙️  Will Byers Wake Word Voice Chat")
    print("=" * 60)
    print(f"Say '{args.wake_word}' to activate!")
    print("Will will respond through the lights!")
    if LED_AVAILABLE:
        print("Responses will be flashed on the LEDs.")
    else:
        print("Running in terminal-only mode (LED hardware not connected).")
    if not VOSK_AVAILABLE:
        print("\n⚠️  WARNING: Vosk not installed!")
        print("Install with: pip install vosk")
        print("Wake word detection will not work.\n")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    # Check if vosk is available
    if not VOSK_AVAILABLE:
        print("\n❌ Cannot start: Vosk is required for wake word detection.")
        print("Install it with: pip install vosk")
        return

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

    print(f"\n🎧 Ready! Say '{args.wake_word}' to start...\n")

    try:
        while True:
            # Listen for wake word
            wake_word_detected = listen_for_wake_word(
                wake_word=args.wake_word,
                sensitivity=args.sensitivity
            )
            
            if not wake_word_detected:
                # User pressed Ctrl+C during wake word listening
                break
            
            # Flash lights to acknowledge wake word
            quick_flash_acknowledgment()
            
            # Record audio for fixed duration
            audio = record_audio_fixed_duration(duration=args.record_duration)

            # Transcribe using appropriate method
            if remote_server:
                transcription = transcribe_audio_remote(audio, remote_server)
            else:
                transcription = transcribe_audio_local(audio, model)

            if not transcription:
                print("❌ No speech detected. Please try again.")
                print(f"\n👂 Listening for wake word: '{args.wake_word}'...\n")
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
            
            # Ready for next wake word
            print(f"\n👂 Listening for wake word: '{args.wake_word}'...\n")
            
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        if LED_AVAILABLE and pixels is not None:
            pixels.fill((0, 0, 0))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please try again.")

if __name__ == "__main__":
    main()