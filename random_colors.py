#!/usr/bin/env python

import board
import neopixel
import string
import time
import numpy as np

pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 150

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, pixel_order=ORDER
)

char_to_pixel_map = {ch: i for i,ch in enumerate(string.ascii_lowercase)}

colors = [(0,0,0)] * num_pixels

while True:
   color = np.asarray(np.random.dirichlet((1,1,1))*255,dtype=int)
   i = np.random.choice(range(num_pixels),1)
   pixels[int(i)] = color


