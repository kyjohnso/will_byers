#!/usr/bin/env python3
"""
Check available audio devices and their supported sample rates.
"""

import sounddevice as sd

print("=" * 60)
print("Available Audio Devices")
print("=" * 60)
print(sd.query_devices())

print("\n" + "=" * 60)
print("Default Input Device")
print("=" * 60)
default_input = sd.query_devices(kind='input')
print(default_input)

print("\n" + "=" * 60)
print("Testing Common Sample Rates")
print("=" * 60)

# Test common sample rates
sample_rates = [8000, 16000, 22050, 44100, 48000]

for rate in sample_rates:
    try:
        sd.check_input_settings(samplerate=rate, channels=1)
        print(f"✓ {rate} Hz - SUPPORTED")
    except Exception as e:
        print(f"✗ {rate} Hz - not supported")
