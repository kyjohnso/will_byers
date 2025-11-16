#!/usr/bin/env python3
"""
Test script to record audio and transcribe it using Whisper.
This is a simple test before integrating into the full voice chat.
"""

import sounddevice as sd
import scipy.io.wavfile as wavfile
import whisper
import numpy as np
import tempfile
import os

# Recording parameters
DURATION = 5  # seconds
SAMPLE_RATE = 48000  # 48kHz (USB mic requirement, Whisper will resample internally)
CHANNELS = 1  # mono

def record_audio(duration=DURATION):
    """Record audio for the specified duration."""
    print(f"\n🎤 Recording for {duration} seconds...")
    print("SPEAK NOW!")

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

if __name__ == "__main__":
    print("=" * 60)
    print("🎙️  Audio Recording and Transcription Test")
    print("=" * 60)

    # Load Whisper model
    print("\n📥 Loading Whisper model (this may take a moment)...")
    print("Using 'base' model (good balance of speed and accuracy)")
    model = whisper.load_model("base")
    print("✓ Model loaded!")

    while True:
        try:
            # Ask user if they want to record
            user_input = input("\nPress ENTER to record, or type 'quit' to exit: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            # Record audio
            audio = record_audio()

            # Transcribe
            transcription = transcribe_audio(audio, model)

            # Display results
            if transcription:
                print(f"\n✅ Transcription: \"{transcription}\"")
            else:
                print("\n❌ No speech detected. Please try again.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")
