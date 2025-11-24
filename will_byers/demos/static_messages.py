#!/usr/bin/env python

import numpy as np
import board
import neopixel
import string
import time
import sys
from pathlib import Path

# Add parent directory to path to import led_config
sys.path.insert(0, str(Path(__file__).parent.parent))
from led_config import load_led_mapping_with_fallback

pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 150

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.9, pixel_order=ORDER
)

# Load character to LED position mapping from JSON file
char_to_pixel_map = load_led_mapping_with_fallback()

message_to_play = "   WHO IS EXCITED FOR THE LAKE DISTRICT   "

seconds_per_character = 0.9
seconds_between_character = 0.2

def play_pixel(i,color,seconds_per_character):
    pixels[i] = color
    time.sleep(seconds_per_character)
    pixels[i] = (0,0,0)

colors = [
    (255,0,0),
    (0,255,0),
    (0,0,255),
    (128,128,128),
]
colors2 = [
    (255,0,0),
    (0,255,0),
    (0,0,255),
    (128,128,128),
    (0,0,0),
    (0,0,0),
    (0,0,0),
]

while True:
    pixels.fill((0,0,0))
    for ich, ch in enumerate(message_to_play):
        if ch == " ":
            pixels.fill((0,0,0))
            time.sleep(3*seconds_between_character)
            continue

        time.sleep(seconds_between_character)
        play_pixel(
            char_to_pixel_map[ch],
            colors[ich % len(colors)],
            seconds_per_character,
        )
    for _ in range(1500):
        color = colors2[int(np.random.choice(range(len(colors2))))]
        i = np.random.choice(range(num_pixels),1)
        pixels[int(i)] = color

    
