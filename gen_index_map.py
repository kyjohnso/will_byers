#!/usr/bin/env python

import board
import neopixel
import string
import time
import numpy as np

pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 100

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, pixel_order=ORDER
)

index_map = {}

pixels.fill((0,0,0))
for i in range(num_pixels):
    pixels[i] = (0,255,0)
    if i != 0:
        pixels[i-1] = (0,0,0)
    index_map[i] = input("letter")

print(index_map)

