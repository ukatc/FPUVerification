#!/usr/bin/env python

# Simple script to control the lamps outside of the VFRIG
# Intended to be used to remotely inspect the vfrig from the webcam

from Lamps import lctrl

if __name__ == "__main__":
    Lamp = lctrl.lampController()

    with Lamp.use_ambientlight():
        input("Ambient light is on, press any key to continue")
