from __future__ import print_function
import time
import argparse
import FpuGridDriver
import ast
from FpuGridDriver import *
from fpu_commands import *
import GigECamera as gig #Alan's prototype camera code
from numpy import *



#this connects to the FPU(s).  If any are missing serial numbers, this will return errors and require you to exit and use fpu-admin to flash/initialise the SR. 
def connect(NUM_FPUS):  

	gd = FpuGridDriver.GridDriver(NUM_FPUS)

	gateway_address = [ FpuGridDriver.GatewayAddress("192.168.0.12", 4700) ] #this address is suitable for the verification rig only		    

	print("\nConnecting grid:", gd.connect(address_list=gateway_address))
	print("Getting grid state:")
	gs = gd.getGridState()
	print(gs)
	print(" - Number of FPUs is ",NUM_FPUS)
	print(" - FPU ID to be moved is", FPU_ID)
	fpusn = gd.printSerialNumbers(gs)
	gd.printFirmwareVersion(gs)
	
	return gd, gs, fpusn

#this executes a motion given relative alpha and beta angles (degrees).  The FPU must be initialised i.e. datumed
def execute_motion(gd, gs, alpha, beta):
	print("Moving alpha",alpha,"degrees and beta",beta,"degrees")
	wf = gen_wf(alpha, beta)
	gd.configMotion(wf,gs)
	gd.executeMotion(gs)
	print("Real positions are:")
	current_angles = gd.trackedAngles(gs, retrieve=True)
        real_alpha = array([x.as_scalar() for x, y in current_angles ])
        real_beta = array([y.as_scalar() for x, y in current_angles ])

	return gs, real_alpha, real_beta

def execute_waveform(gd, gs, man_wf):
	gd.configMotion(man_wf,gs)
	gd.executeMotion(gs)

	return gs

def reverse_waveform(gd,gs):
	gd.reverseMotion(gs)
	gd.executeMotion(gs)

	return gs

# This function takes a certain number of images and stores them to the desired folder. It also increments the imageCounter and returns its value for later use.
def take_images(FOLDER_NAME,imageNumber,numberOfimages):
	for i in range(0,numberOfimages):
		gig.saveImageFromCamera(gig.TEST_CAMERA, "{0:s}{1:03d}.bmp".format(FOLDER_NAME,imageNumber))
		imageNumber = imageNumber + 1 

	return imageNumber

#this runs the test and so is the part which can be modified
#test description:
#positional repeatability using manually concatenated waveforms
def run_test(NUM_FPUS, FPU_ID, WAVEFORMS, FPU_IMGN, FOLDER_NAME):

	gd, gs, fpusn = connect(NUM_FPUS)	
	raw_input("\n --Connected.  Press Enter to initialise FPU(s)...-- \n")

	gd.findDatum(gs)
	raw_input("\n --Initialised.  Press Enter to run test...-- \n")

	# Create a logging number for all the images
	imageCounter = 0

	#zero position
	imageCounter = take_images(FOLDER_NAME, imageCounter, FPU_IMGN)

	print("\n --Moving to zero position-- \n")	

	# First movement to "start position". 
	gs, real_alpha, real_beta = execute_motion(gd,gs,10,-170)
	theo_alpha = -170
	theo_beta = -170

	imageCounter = take_images(FOLDER_NAME, imageCounter, FPU_IMGN)

	print("\n --At zero position--")
	# Cycle through alpha motions

	waveform_raw = "".join(open(WAVEFORMS).read())
	waveform_list = waveform_raw.split("\n")
	i = 0
		
	while i < (len(waveform_list) - 3):
		#raw_input("Execute next waveform")
		print("Executing waveform",waveform_list[i])
		wf = ast.literal_eval(waveform_list[i + 1])
		#print(wf)
		gs = execute_waveform(gd,gs,wf)
		imageCounter = take_images(FOLDER_NAME, imageCounter, FPU_IMGN)
		gs = reverse_waveform(gd,gs)
		imageCounter = take_images(FOLDER_NAME, imageCounter, FPU_IMGN)
		i = i + 3
	

	# Final movement takes both motors back to datum. 
	gs, real_alpha, real_beta = execute_motion(gd,gs,-9,171)
	imageCounter = take_images(FOLDER_NAME,imageCounter,FPU_IMGN)

	# Finally datum
	gd.findDatum(gs)
	imageCounter = take_images(FOLDER_NAME,imageCounter,FPU_IMGN)

	print("\n--Movements complete-- ")

	#calls OpenCV script to output the target coordinates as output.txt in same folder as images saved
	print("--Finding coordinates--\n")	
	import findTargetCoordinates as coor
	coor.main(FOLDER_NAME, False, False)
	print("--Image analysis complete-- \n")
	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'Test positional repeatability')
	parser.add_argument('-n', type=int, help='Number of FPUs on connected backplane, default 1', required=False, default = 1)
	parser.add_argument('-id', type=int, help='CAN address of FPU to be moved, default 0', required=False, default = 0)
	parser.add_argument('-imgn', type=int, help='Number of images to take at each position, default 3', required=False, default = 1)
	parser.add_argument('-waveforms', type=str, help='Location of waveform text file', required=True, default = 0)
	parser.add_argument('-folder', type=str, help='Location to save files, folder must already exist', required=True)

	args = parser.parse_args()

	NUM_FPUS = args.n
	FPU_ID = args.id
	FPU_IMGN = args.imgn
	WAVEFORMS = args.waveforms
	FOLDER_NAME = args.folder

	run_test(NUM_FPUS, FPU_ID, WAVEFORMS, FPU_IMGN, FOLDER_NAME)	
	
	






      









