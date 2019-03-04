from __future__ import print_function, division
from numpy import nan

import cv2
from math import pi, sqrt
from matplotlib import pyplot as plt

from DistortionCorrection import correct
from ImageAnalysisFuncs.base import ImageAnalysisError


# exceptions which are raised if image analysis functions fail

class RepeatabilityAnalysisError(ImageAnalysisError):
    pass

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

POSITIONAL_REPEATABILITY_ALGORITHM_VERSION = 0.1
DATUM_REPEATABILITY_ALGORITHM_VERSION = 0.1

def posrepCoordinates(image_path,
	              #configurable parameters
	              POSREP_PLATESCALE=0.02361, #mm per pixel
	              POSREP_SMALL_DIAMETER=1.5, #mm 
	              POSREP_LARGE_DIAMETER=2.5, #mm 
	              POSREP_DIAMETER_TOLERANCE=0.1, #mm 
	              POSREP_THRESHOLD=40, #0-255
	              POSREP_QUALITY_METRIC=0.8, #dimensionless
	              POSREP_CALIBRATION_PARS=None,
	              verbosity=0, # a value > 5 will write contour parameters to terminal
	              display=False): #will display image with contours annotated
        
        """reads an image from the positional repeatability camera and returns 
        the XY coordinates and circularity of the two targets in mm"""

        # Authors: Stephen Watson (initial algorithm March 4, 2019)
        # Johannes Nix (code imported and re-formatted)


	smallPerimeterLo = (POSREP_SMALL_DIAMETER - POSREP_DIAMETER_TOLERANCE) * pi / POSREP_PLATESCALE
	smallPerimeterHi = (POSREP_SMALL_DIAMETER + POSREP_DIAMETER_TOLERANCE) * pi / POSREP_PLATESCALE
	largePerimeterLo = (POSREP_LARGE_DIAMETER - POSREP_DIAMETER_TOLERANCE) * pi / POSREP_PLATESCALE
	largePerimeterHi = (POSREP_LARGE_DIAMETER + POSREP_DIAMETER_TOLERANCE) * pi / POSREP_PLATESCALE

	if verbosity > 5:
		print ("Lower/upper perimeter limits of small & large "
                       "targets in mm: %.2f / %.2f ; %.2f / %.2f" % (
                               smallPerimeterLo, smallPerimeterHi, largePerimeterLo, largePerimeterHi))

	centres = {}

	image = cv2.imread(image_path)

        image = correct(image, calibration_pars=POSREP_CALIBRATION_PARS)

	#image processing
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blur = cv2.GaussianBlur(gray, (9, 9), 0)
	thresh = cv2.threshold(blur, POSREP_THRESHOLD, 255, cv2.THRESH_BINARY)[1] 
	
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
		if circularity > POSREP_QUALITY_METRIC:
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
			
			#finds contour momenIA.posrepCoordinates("./PT25_posrep_1_001.bmp")ts,
                        # which can be used to derive centre of mass		
			M = cv2.moments(c)
			cX = M["m10"] / M["m00"]
			cY = M["m01"] / M["m00"]
			centres[circle] = (cX, cY, circularity, i)

			#superimpose contours and labels onto original image, user prompt required in terminal to progress
			if display == True:
				cv2.drawContours(image, cnts, -1, (0, 255, 0), 2)
				label = str(i) + ", " + str(round(perimeter,1)) + ", " + str(round(circularity,2)) + " = " + circle
				cv2.putText(image,label,(int(cX),int(cY)),cv2.FONT_HERSHEY_SIMPLEX ,2,(255,255,255),2,1)
				cv2.imshow('image', cv2.resize(image, (0,0), fx=0.3, fy=0.3))
				cv2.waitKey(100)
				raw_input("Press enter to continue")

	if multipleSmall == True:
		raise RepeatabilityAnalysisError("Multiple small targets found - tighten parameters or use "
                                "display option to investigate images for contamination")
	if multipleLarge == True: 
		raise RepeatabilityAnalysisError("Multiple large targets found - tighten parameters or"
                                " use display option to investigate images for contamination")
        
	if smallTargetFound == False:
		raise RepeatabilityAnalysisError("Small target not found - "
                                                 "loosen diameter tolerance or change image thresholding")
        
	if largeTargetFound == False:
		raise RepeatabilityAnalysisError("Large target not found - "
                                                 "loosen diameter tolerance or change image thresholding")

	if verbosity > 5:
                print("Contour %i = small target, contour %i = large target" %(
                        centres['Small Target'][3], centres['Large Target'][3]))

	posrep_small_target_x = centres['Small Target'][0] * POSREP_PLATESCALE
	posrep_small_target_y = centres['Small Target'][1] * POSREP_PLATESCALE
	posrep_small_target_quality = centres['Small Target'][2]
	posrep_large_target_x = centres['Large Target'][0] * POSREP_PLATESCALE
	posrep_large_target_y = centres['Large Target'][1] * POSREP_PLATESCALE
	posrep_large_target_quality = centres['Large Target'][2]

	#target separation check - the values here are not configurable, as
        # they represent real mechanical tolerances
	targetSeparation = sqrt((posrep_small_target_x - posrep_large_target_x)**2 +
                                (posrep_small_target_y - posrep_large_target_y)**2)
	if verbosity > 5:
                print("Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm." % targetSeparation)
	if targetSeparation > 2.475 or targetSeparation < 2.275:
		raise RepeatabilityAnalysisError("Target separation is out of spec - "
                                "use display option to check for target-like reflections")

	return (posrep_small_target_x,
                posrep_small_target_y,
                posrep_small_target_quality,
                posrep_large_target_x,
                posrep_large_target_y,
                posrep_large_target_quality)



def evaluate_datum_repeatability(unmoved_coords, datumed_coords, moved_coords):
    """Takes three lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.
    
    """

    return 0.005



def evaluate_positional_repeatability(dict_of_coordinates, POSITION_REP_PASS=None):
    """Takes a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm 
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are dimensionless counts (for alpha_steps and beta_steps) 
    and millimeter (for x_measured and y_measured).

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    return 0.005



def evaluate_positional_verification(dict_of_coordinates, POSITION_VER_PASS=None):
    """Takes a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm 
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are in dimensionless counts (for alpha_steps and beta_steps) 
    and millimeter (for x_measured and y_measured).

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    return 0.005



