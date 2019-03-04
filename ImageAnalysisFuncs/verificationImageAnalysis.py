
import cv2
from math import pi, sqrt
import argparse
import numpy as np
from numpy.polynomial import Polynomial
from matplotlib import pyplot as plt

from ImageAnalysisFuncs import correct

__version__ = 0.1
__date__ = 190304
__author__ = "Steve Watson"

def pupalnCoordinates(image_path,
	              #configurable parameters
	              PUPALN_PLATESCALE=0.00668, #mm per pixel
	              PUPALN_CIRCULARITY_THRESH=0.8, #dimensionless
	              PUPALN_NOISE_METRIC=0,
	              PUPALN_CALIBRATION_PARS=None,
	              verbosity=0, # a value > 5 will write contour parameters to terminal
	              display=False): #will display image with contours annotated

        """reads an image from the pupil alignment camera and returns the 
        XY coordinates and circularity of the projected dot in mm
        """



	image = cv2.imread(image_path)

	#image processing
	#APPLY DISTORTION CORRECTION
        image = correct(image, calibration_pars=PUPALN_CALIBRATION_PARS)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	PUPALN_SPOT_X = 0
	PUPALN_SPOT_Y = 0
	PUPALN_QUALITY = 0

	#exceptions

	return PUPALN_SPOT_X, PUPALN_SPOT_Y, PUPALN_QUALITY


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
		raise Exception("Multiple small targets found - tighten parameters or use "
                                "display option to investigate images for contamination")
	if multipleLarge == True: 
		raise Exception("Multiple large targets found - tighten parameters or"
                                " use display option to investigate images for contamination")
        
	if smallTargetFound == False:
		raise Exception("Small target not found - loosen diameter tolerance or change image thresholding")
        
	if largeTargetFound == False:
		raise Exception("Large target not found - loosen diameter tolerance or change image thresholding")

	if verbosity > 5:
                print("Contour %i = small target, contour %i = large target" %(
                        centres['Small Target'][3], centres['Large Target'][3]))

	POSREP_SMALL_TARGET_X = centres['Small Target'][0] * POSREP_PLATESCALE
	POSREP_SMALL_TARGET_Y = centres['Small Target'][1] * POSREP_PLATESCALE
	POSREP_SMALL_TARGET_QUALITY = centres['Small Target'][2]
	POSREP_LARGE_TARGET_X = centres['Large Target'][0] * POSREP_PLATESCALE
	POSREP_LARGE_TARGET_Y = centres['Large Target'][1] * POSREP_PLATESCALE
	POSREP_LARGE_TARGET_QUALITY = centres['Large Target'][2]

	#target separation check - the values here are not configurable, as
        # they represent real mechanical tolerances
	targetSeparation = sqrt((POSREP_SMALL_TARGET_X - POSREP_LARGE_TARGET_X)**2 +
                                (POSREP_SMALL_TARGET_Y - POSREP_LARGE_TARGET_Y)**2)
	if verbosity > 5:
                print("Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm." % targetSeparation)
	if targetSeparation > 2.475 or targetSeparation < 2.275:
		raise Exception("Target separation is out of spec - "
                                "use display option to check for target-like reflections")

	return (POSREP_SMALL_TARGET_X,
                POSREP_SMALL_TARGET_Y,
                POSREP_SMALL_TARGET_QUALITY,
                POSREP_LARGE_TARGET_X,
                POSREP_LARGE_TARGET_Y,
                POSREP_LARGE_TARGET_QUALITY)


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
		raise Exception("Multiple small targets found - tighten parameters or investigate images for contamination")
        
	if multipleLarge == True: 
		raise Exception("Multiple large targets found - tighten parameters or investigate images for contamination")
        
	if smallTargetFound == False:
		raise Exception("Small target not found - loosen diameter tolerance or change image thresholding")
        
	if largeTargetFound == False:
		raise Exception("Large target not found - loosen diameter tolerance or change image thresholding")

	if verbosity > 5:
                print("Contour %i = small target, contour %i = large target" %(centres['Small Target'][3], centres['Large Target'][3]))

	METCAL_SMALL_TARGET_X = centres['Small Target'][0] * METCAL_PLATESCALE
	METCAL_SMALL_TARGET_Y = centres['Small Target'][1] * METCAL_PLATESCALE
	METCAL_SMALL_TARGET_QUALITY = centres['Small Target'][2]
	METCAL_LARGE_TARGET_X = centres['Large Target'][0] * METCAL_PLATESCALE
	METCAL_LARGE_TARGET_Y = centres['Large Target'][1] * METCAL_PLATESCALE
	METCAL_LARGE_TARGET_QUALITY = centres['Large Target'][2]

	# target separation check - the values here are not configurable,
        # as they represent real mechanical tolerances
	targetSeparation = sqrt((METCAL_SMALL_TARGET_X - METCAL_LARGE_TARGET_X)**2 +
                                (METCAL_SMALL_TARGET_Y - METCAL_LARGE_TARGET_Y)**2)
        
	if verbosity > 5:
                print("Target separation is %.3f mm.  Specification is 2.375 +/- 0.1 mm." % targetSeparation)
                
	if targetSeparation > 2.475 or targetSeparation < 2.275:
		raise Exception("Target separation is out of spec - use display option "
                                "to check for target-like reflections")

	return (METCAL_SMALL_TARGET_X,
                METCAL_SMALL_TARGET_Y,
                METCAL_SMALL_TARGET_QUALITY,
                METCAL_LARGE_TARGET_X,
                METCAL_LARGE_TARGET_Y,
                METCAL_LARGE_TARGET_QUALITY)


def metcalFibreCoordinates(image_path,
	                   #configurable parameters
	                   METCAL_PLATESCALE=0.00668, #mm per pixel
	                   METCAL_QUALITY_METRIC=0.8, #dimensionless

	                   verbosity=0, # a value > 5 will write contour parameters to terminal
	                   display=False): #will display image with contours annotated

        """reads an image from the metrology calibration camera and returns the 
        XY coordinates and Gaussian fit quality of the backlit fibre in mm"""


	image = cv2.imread(image_path)

	#image processing
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	METCAL_FIBRE_X = 0
	METCAL_FIBRE_Y = 0
	METCAL_FIBRE_QUALITY = 0

	#exceptions

	return METCAL_FIBRE_X, METCAL_FIBRE_Y, METCAL_FIBRE_QUALITY


def methtHeight(image_path,	#configurable parameters
	        METHT_PLATESCALE=0.00668, #mm per pixel
	        METHT_THRESHOLD=150, #0-255
	        METHT_SCAN_HEIGHT=2000, #pixels
	        METHT_GAUSS_BLUR=1, #pixels - MUST BE AN ODD NUMBER
	        METHT_STANDARD_DEV=0.04, #mm
	        METHT_NOISE_METRIC=0.25, #dimensionless

	        verbosity=0, # a value > 5 will write relevant parameters to the terminal
	        display=False): #will thresholded image

        """reads an image from the metrology height camera and 
        returns the heights and quality metric of the two targets in mm"""


	#image processing
	image = cv2.imread(image_path)
	blur = cv2.GaussianBlur(image, (METHT_GAUSS_BLUR, METHT_GAUSS_BLUR), 0)
	gray = cv2.cvtColor(blur,cv2.COLOR_BGR2GRAY)
	gray = np.float32(gray)

	tval, thresh = cv2.threshold(gray, METHT_THRESHOLD, 255, 0, cv2.THRESH_BINARY)

	#find location of beta arm
	betaScan = thresh[METHT_SCAN_HEIGHT,:]
	betaSide = 0
	for i in range(0,len(betaScan) - 1):
		if (betaScan[i + 1] - betaScan[i]) < 0:
			betaSide = i
			if verbosity > 5:
                                print ("Beta arm side is at x-coordinate %i" % betaSide)   

	if betaSide == 0:
		raise Exception("Beta arm side not found - consider changing scan height")

	threshcrop = thresh[1750:2700, betaSide - 100:betaSide + 1500]	
	if display == True:
		plt.imshow(threshcrop)
		plt.title('Thresholded image, thresholdVal = %i' % thresholdVal)
		plt.show()

	#estimation of noise in thresholded image
	threshblur = cv2.GaussianBlur(threshcrop, (3,3), 0)
	threshave, threshstd = cv2.meanStdDev(threshcrop)
	threshblurave, threshblurstd = cv2.meanStdDev(threshblur)
	noiseMetric = (threshstd - threshblurstd) / threshblurstd * 100

	if verbosity > 5:
                print ("Noise metric in thresholded image is %.2f" % noiseMetric)

	#pixel distances from side of beta arm to measurement points
	#these parameters could be made configurable but shouldn't need to be changed
	armSurfaceX = [60,320,760,980,1220]
	smallTargetX =[100,180,260]
	largeTargetX = [380,530,680]

	#fills lists with pixel values at X coordinates defined above
	armSurfacePix,smallTargetPix,largeTargetPix = [],[],[]	
	for i in range(0,5):
		armSurfacePix.append(thresh[:,betaSide + armSurfaceX[i]])
	for i in range(0,3):
		smallTargetPix.append(thresh[:,betaSide + smallTargetX[i]])
		largeTargetPix.append(thresh[:,betaSide + largeTargetX[i]])

	#looks for pixel transitions indicating surfaces
	armSurfaceY,smallTargetY,largeTargetY = [None]*5,[None]*3,[None]*3
	for i in range(0,5):
		for p in range (0,len(thresh) - 1):
			if abs(armSurfacePix[i][p+1] - armSurfacePix[i][p]) > 0:
				armSurfaceY[i] = p
				break
	for i in range(0,3):
		for p in range (0,len(thresh) - 1):
			if abs(smallTargetPix[i][p+1] - smallTargetPix[i][p]) > 0:
				smallTargetY[i] = p
				break
	for i in range(0,3):
		for p in range (0,len(thresh) - 1):
			if abs(largeTargetPix[i][p+1] - largeTargetPix[i][p]) > 0:
				largeTargetY[i] = p
				break
	if verbosity > 5:
		print("Arm surface points found - x:%s y:%s" % (armSurfaceX, armSurfaceY))
		print("Small target points found - x:%s y:%s" % (smallTargetX, smallTargetY))
		print("Large target points found - x:%s y:%s" % (largeTargetX, largeTargetY))

	#best fit straight line through 5 beta arm surface points
	armSurfaceDom = Polynomial.fit(armSurfaceX,armSurfaceY,1, domain=(-1,1))
	armSurface = armSurfaceDom.convert().coef

	#calculates normal distance from points on targets to beta arm surface
	#D = |a*x_n + b*y_n + c|/sqrt(a^2 + b^2) where line is defined as ax + by + c = 0
	a = armSurface[1]
	b = -1
	c = armSurface[0]
	smallTargetHeights,largeTargetHeights = [None]*3,[None]*3
	for i in range(0,3):
		smallTargetHeights[i] = (a * smallTargetX[i] + b * smallTargetY[i] + c)/sqrt(a**2 + b**2)
		largeTargetHeights[i] = (a * largeTargetX[i] + b * largeTargetY[i] + c)/sqrt(a**2 + b**2)

	#calculates standard deviation of heights to see how level the targets are
	stdSmallTarget = np.std(smallTargetHeights) * METHT_PLATESCALE
	stdLargeTarget = np.std(largeTargetHeights) * METHT_PLATESCALE
	if verbosity > 5:
                print ("Standard deviations of small/large target heights are %.3f and %.3f" %
                       (stdSmallTarget, stdLargeTarget))

	#exceptions
	if stdSmallTarget > METHT_STANDARD_DEV:
		raise Exception("Small target points have high standard deviation - target may not be sitting flat")
        
	if stdLargeTarget > METHT_STANDARD_DEV:
		raise Exception("Large target points have high standard deviation - target may not be sitting flat")
        
	if noiseMetric > METHT_NOISE_METRIC:
		raise Exception("Image noise excessive - consider changing Gaussian blur value")

	METHT_SMALL_TARGET_HEIGHT = sum(smallTargetHeights)/len(smallTargetHeights) * METHT_PLATESCALE
	METHT_LARGE_TARGET_HEIGHT = sum(largeTargetHeights)/len(largeTargetHeights) * METHT_PLATESCALE

	return METHT_SMALL_TARGET_HEIGHT, METHT_LARGE_TARGET_HEIGHT



