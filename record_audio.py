#!/usr/bin/env python3
"""
Simple audio recorder that captures 10 seconds of audio from a microphone.
"""

import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from datetime import datetime

# Recording parameters
DURATION = 10  # seconds
SAMPLE_RATE = 44100  # Hz
CHANNELS = 1  # mono

def record_audio(duration=DURATION, sample_rate=SAMPLE_RATE):
    """Record audio for the specified duration."""
    print(f"Recording for {duration} seconds...")
    print("Speak now!")

    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=CHANNELS,
        dtype=np.int16
    )

    # Wait until recording is finished
    sd.wait()

    print("Recording finished!")
    return audio_data

def save_audio(audio_data, filename=None, sample_rate=SAMPLE_RATE):
    """Save the recorded audio to a WAV file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"

    wavfile.write(filename, sample_rate, audio_data)
    print(f"Audio saved to: {filename}")
    return filename

if __name__ == "__main__":
    try:
        # Record audio
        audio = record_audio()

        # Save to file
        save_audio(audio)

    except KeyboardInterrupt:
        print("\nRecording cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have the required packages installed:")
        print("  pip install sounddevice scipy numpy")
