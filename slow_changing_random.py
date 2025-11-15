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

pixels.fill((0,255,0))

colors = [np.array([0,255,0])]*num_pixels

n_steps = 15

bins = np.arange(255)

new_color = np.random.dirichlet((1,1,1))*255
delta_color = (new_color - colors[0])/n_steps

while True:
    print(colors[0],new_color)
    print(np.abs(colors[0]-new_color)<2*np.abs(delta_color))
    if (np.abs(colors[0]-new_color)<2*np.abs(delta_color)).all():
        new_color = np.asarray(np.random.dirichlet((1,1,1))*255,dtype=int)
        delta_color = (new_color - colors[0])/n_steps
        print(new_color)

    for i in range(num_pixels-1,0,-1):
        colors[i] = colors[i-1]

    colors[0] = colors[0] + delta_color
    
    for i in range(num_pixels):
        color = tuple(
            np.digitize(colors[i],bins)
        )
        pixels[i] = color
