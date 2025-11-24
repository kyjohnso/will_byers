#!/usr/bin/env python

import numpy as np
import board
import neopixel
import string
import time

pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 150

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.9, pixel_order=ORDER
)

char_to_pixel_map = {ch: i for i,ch in enumerate(string.ascii_lowercase)}

char_to_pixel_map = {'R': 11, 'S': 15, 'T': 18, 'U': 21, 'V': 24, 'W': 27, 'X': 31, 'Y': 33, 'Z': 36, 'Q': 44, 'P': 47, 'O': 49, 'N': 50, 'M': 53, 'L': 57, 'K': 59, 'J': 62, 'I': 65, 'A': 73, 'B': 76, 'C': 80, 'D': 83, 'E': 87, 'F': 90, 'G': 92, 'H': 95}

messages_to_play = [
    " HAPPY HALLOWEEN HARROGATE ",
    " BOOOOOOO ",
    " THE CALL IS COMING FROM INSIDE THE HOUSE ",
    " I AM RIGHT HERE      R U N ",
]

seconds_per_character = 0.9
seconds_between_character = 0.2

def play_pixel(i,color,seconds_per_character):
    pixels[i] = color
    time.sleep(seconds_per_character)
    pixels[i] = (0,0,0)

colors = [
    (35,255,0),
#    (255,0,0),
#    (0,255,0),
#    (0,0,255),
#    (128,128,128),
]
colors2 = [
    (35,255,0),
    (35,255,0),
    (35,255,0),
    (0,148,211),
    (0,0,0),
    (0,0,0),
    (0,0,0),
]

while True:
    pixels.fill((0,0,0))
    message_to_play = messages_to_play[
        int(np.random.choice(range(len(messages_to_play))))]

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

    
