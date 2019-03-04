from __future__ import print_function, division
from numpy import nan

import cv2
from math import pi, sqrt
import numpy as np
from numpy.polynomial import Polynomial
from matplotlib import pyplot as plt


from ImageAnalysisFuncs.base import ImageAnalysisError

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

METROLOGY_ANALYSIS_ALGORITHM_VERSION = 0.1


# exceptions which are raised if image analysis functions fail

class MetrologyAnalysisTargetError(ImageAnalysisError):
    pass

class MetrologyAnalysisFibreError(ImageAnalysisError):
    pass


def metcalTargetCoordinates(image_path,
	                    #configurable parameters
	                    METCAL_PLATESCALE=0.00668, #mm per pixel
	                    METCAL_SMALL_DIAMETER=1.5, #mm
	                    METCAL_LARGE_DIAMETER=2.5, #mm 
	                    METCAL_DIAMETER_TOLERANCE=0.1, #mm 
	                    METCAL_GAUSS_BLUR=3, #pixels - MUST BE AN ODD NUMBER
	                    METCAL_THRESHOLD=40,  #0-255
	                    METCAL_QUALITY_METRIC=0.8, #dimensionless                            
	                    verbosity=0, # a value > 5 will write contour parameters to terminal
	                    display=False): #will display image with contours annotated

        """reads an image from the metrology calibration camera and returns 
        the XY coordinates and circularity of the two targets in mm"""

        # Authors: Stephen Watson (initial algorithm March 4, 2019)
        # Johannes Nix (code imported and re-formatted)

	smallPerimeterLo = (METCAL_SMALL_DIAMETER - METCAL_DIAMETER_TOLERANCE) * pi / METCAL_PLATESCALE
	smallPerimeterHi = (METCAL_SMALL_DIAMETER + METCAL_DIAMETER_TOLERANCE) * pi / METCAL_PLATESCALE
	largePerimeterLo = (METCAL_LARGE_DIAMETER - METCAL_DIAMETER_TOLERANCE) * pi / METCAL_PLATESCALE
	largePerimeterHi = (METCAL_LARGE_DIAMETER + METCAL_DIAMETER_TOLERANCE) * pi / METCAL_PLATESCALE

	if verbosity > 5:
		print ("Lower/upper perimeter limits of small & large targets in mm: %.2f / %.2f ; %.2f / %.2f" % (
                        smallPerimeterLo, smallPerimeterHi, largePerimeterLo, largePerimeterHi))

	centres = {}

	image = cv2.imread(image_path)

	#image processing
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blur = cv2.GaussianBlur(gray, (METCAL_GAUSS_BLUR, METCAL_GAUSS_BLUR), 0)
	thresh = cv2.threshold(blur, METCAL_THRESHOLD, 255, cv2.THRESH_BINARY)[1] 
	
	#find contours from thresholded image
	cnts = sorted(cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1],
                      key=cv2.contourArea, reverse=True)[:15]
	
	largeTargetFound, smallTargetFound, multipleSmall, multipleLarge = False, False, False, False

	# filter through contours on size and circularity	
	for i, c in enumerate(cnts):
		perimeter = cv2.arcLength(c, True)
		area = cv2.contourArea(c)
		if area > 0 and perimeter > 0:
			circularity = 4 * pi * (area / (perimeter * perimeter))
		if verbosity > 5:
			print ("ContourID - %i; perimeter - %.2f; circularity - %.2f" % (i, perimeter, circularity))		
		if circularity > METCAL_QUALITY_METRIC:
			if perimeter > smallPerimeterLo and perimeter < smallPerimeterHi:	
				if smallTargetFound == True: multipleSmall = True	
				circle = 'Small Target'
				smallTargetFound = True
			elif perimeter > largePerimeterLo and perimeter < largePerimeterHi:
				if largeTargetFound == True: multipleLarge = True
				circle = 'Large Target'
				largeTargetFound = True
			else:
				circle = "N" + str(i)
			
			#finds contour moments, which can be used to derive centre of mass		
			M = cv2.moments(c)
			cX = M["m10"] / M["m00"]
			cY = M["m01"] / M["m00"]
			centres[circle] = (cX, cY, circularity, i)

			if display == True:
				cv2.drawContours(image, cnts, -1, (0, 255, 0), 2)
				label = str(i) + ", " + str(round(perimeter,1)) + ", " + str(round(circularity,2)) + " = " + circle
				cv2.putText(image,label,(int(cX),int(cY)),cv2.FONT_HERSHEY_SIMPLEX ,2,(255,255,255),2,1)
				cv2.imshow('image', cv2.resize(image, (0,0), fx=0.3, fy=0.3))
				cv2.waitKey(100)
				raw_input("Press enter to continue")

	if multipleSmall == True:
		raise MetrologyAnalysisTargetError("Multiple small targets found - tighten"
                                                   " parameters or investigate images for contamination")
        
	if multipleLarge == True: 
		raise MetrologyAnalysisTargetError("Multiple large targets found - tighten "
                                                   "parameters or investigate images for contamination")
        
	if smallTargetFound == False:
		raise MetrologyAnalysisTargetError("Small target not found - loosen diameter"
                                                   " tolerance or change image thresholding")
        
	if largeTargetFound == False:
		raise MetrologyAnalysisTargetError("Large target not found - loosen diameter"
                                                   " tolerance or change image thresholding")

	if verbosity > 5:
                print("Contour %i = small target, contour %i = large target" %(
                    centres['Small Target'][3], centres['Large Target'][3]))

	metcal_small_target_x = centres['Small Target'][0] * METCAL_PLATESCALE
	metcal_small_target_y = centres['Small Target'][1] * METCAL_PLATESCALE
	metcal_small_target_quality= centres['Small Target'][2]
	metcal_large_target_x = centres['Large Target'][0] * METCAL_PLATESCALE
	metcal_large_target_y = centres['Large Target'][1] * METCAL_PLATESCALE
	metcal_large_target_quality = centres['Large Target'][2]

	# target separation check - the values here are not configurable,
        # as they represent real mechanical tolerances
	targetSeparation = sqrt((metcal_small_target_x - metcal_large_target_x)**2 +
                                (metcal_small_target_y - metcal_large_target_y)**2)
        
	if verbosity > 5:
                print("Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm." % targetSeparation)
                
	if targetSeparation > 2.475 or targetSeparation < 2.275:
		raise MetrologyAnalysisTargetError("Target separation is out of spec - use display option "
                                "to check for target-like reflections")

	return (metcal_small_target_x,
                metcal_small_target_y,
                metcal_small_target_quality,
                metcal_large_target_x,
                metcal_large_target_y,
                metcal_large_target_quality)


def metcalFibreCoordinates(image_path,
	                   #configurable parameters
	                   METCAL_PLATESCALE=0.00668, #mm per pixel
	                   METCAL_QUALITY_METRIC=0.8, #dimensionless

	                   verbosity=0, # a value > 5 will write contour parameters to terminal
	                   display=False): #will display image with contours annotated

        """reads an image from the metrology calibration camera and returns the 
        XY coordinates and Gaussian fit quality of the backlit fibre in mm"""

        # Authors: Stephen Watson (initial algorithm March 4, 2019)
        # Johannes Nix (code imported and re-formatted)

	image = cv2.imread(image_path)

	#image processing
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	metcal_fibre_x = 0
	metcal_fibre_y = 0
	metcal_fibre_quality = 0

	#exceptions: MetrologyAnalysisFibreError()

	return metcal_fibre_x, metcal_fibre_y, metcal_fibre_quality




def fibre_target_distance(big_target_coords, small_target_coords, fibre_coords):
    """
    takes coordinates of the big metrology target, the small metrology target,
    and the distance in millimeter, and returns the distance between the
    metrology targets and the fibre aperture in millimeter.
    """

    # Authors: Stephen Watson (initial algorithm March 4, 2019)

        
    return 10.0
