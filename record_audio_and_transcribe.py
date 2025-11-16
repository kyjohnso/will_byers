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
import threading

# Recording parameters
SAMPLE_RATE = 48000  # 48kHz (USB mic requirement, Whisper will resample internally)
CHANNELS = 1  # mono

def record_audio_until_enter():
    """Record audio until user presses Enter."""
    print("\n🎤 Recording... Press ENTER to stop!")

    # Storage for recorded chunks
    recording = []
    stop_event = threading.Event()

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
            user_input = input("\nPress ENTER to start recording (or type 'quit' to exit): ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            # Record audio
            audio = record_audio_until_enter()

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
