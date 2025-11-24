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

colors = [
   (255,255,255), # white
   (255,0,0), # green
   (0,255,0), # red
   (0,0,255), # blue
   (255,255,0), # yellow ?
   (255,0,255), # cyan
   (0,255,255), # magenta
   (32,255,64), # hannahs perfect pink
]



while True:
   #color = np.asarray(np.random.dirichlet((1,1,1))*255,dtype=int)
   color_i = np.random.choice(range(len(colors)))
   color = colors[color_i]
   i = np.random.choice(range(num_pixels),1)
   pixels[int(i)] = color


