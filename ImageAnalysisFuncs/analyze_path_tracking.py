# -*- coding: utf-8 -*-
#
# Combines all the images written by the path tracking in one folder
# into a single image.
#
from __future__ import division, print_function

import os
import math
import numpy as np
import cv2



import os

def blend_images_in_folder( folder, newfile ):
    """
    
    Blends all the images found in the given folder and saves them
    to a single, combined image.
    
    """
    nimages = len(list(os.listdir(folder)))
    print("There are", nimages, "images.")
    wcount = 1
    newimg = None
    for filename in os.listdir(folder):

        print("Reading image", wcount, "from", filename)
        img = cv2.imread(os.path.join(folder, filename), 1)

        if newimg is None:
            #Start with the first image
            newimg = img
        else:
            # Blend subsequent images.
            thisweight = 1.0 / float(wcount)
            #thisweight = 1.0 / float(nimages)
            otherweight = 1.0 - thisweight
            newimg = cv2.addWeighted(img, thisweight, newimg, otherweight, 0)
            wcount += 1
            
    cv2.imwrite(newfile, newimg)
    print(wcount, "images blended together and saved to", newfile)
