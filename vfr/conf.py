from __future__ import print_function, division


ALPHA_DATUM_OFFSET = -180
 
DB_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

LAMP_WARMING_TIME_MILLISECONDS = 1000.0

NR360_SERIALNUMBER = 40873952

MTS50_SERIALNUMBER = 83822910

IMAGE_ROOT_FOLDER = '/moonsdata/verification/images'

POS_REP_CAMERA_IP_ADDRESS = "169.254.187.121"

MET_CAL_CAMERA_IP_ADDRESS = "169.254.189.121"

MET_HEIGHT_CAMERA_IP_ADDRESS = "169.254.190.121"

PUPIL_ALGN_CAMERA_IP_ADDRESS = "169.254.108.113"



DATUM_REP_MEASUREMENT_PARS = { 'DATUM_REP_ITERATIONS' : 10, #  – the
                               # number of datum operations made for
                               # each test
                   'DATUM_REP_PASS' : 20.0 ,  # – the maximum single
                               # deviation in microns from the
                               # baseline position which represents an
                               # acceptable FPU
                   'DATUM_REP_EXPOSURE_MS' : 500, # – the exposure
                               # time in milliseconds for a correctly
                               # exposed image
                   'POS_REP_POSITIONS' : [14 + k * 30 for  k in range(6)],
}


MET_CAL_MEASUREMENT_PARS = {
    'METROLOGY_CAL_POSITIONS' =  [268, 328, 28, 88, 148, 208],

    # rotary stage angle, in degrees, required to place each FPU under
    # the metrology calibration camera
    
    'METROLOGY_CAL_TARGET_EXPOSURE_MS' = 500.0, # he exposure time in
                                                # milliseconds for a
                                                # correctly exposed
                                                # image of the
                                                # illuminated targets
    
    'METROLOGY_CAL_FIBRE_EXPOSURE_MS' = 0.1, # he exposure time in
                                             # milliseconds for a
                                             # correctly exposed image
                                             # of the illuminated
                                             # targets
    
    'METROLOGY_CAL_BACKLIGHT_VOLTAGE' = 0.1, # voltage of backlight
                                             # for fibre measurements
}


POSREP_ANALYSIS_PARS = {
	              'POSREP_PLATESCALE' : 0.02361, #mm per pixel
	              'POSREP_SMALL_DIAMETER' : 1.5, #mm 
	              'POSREP_LARGE_DIAMETER' : 2.5, #mm 
	              'POSREP_DIAMETER_TOLERANCE' : 0.1, #mm 
	              'POSREP_THRESHOLD' : 40, #0-255
	              'POSREP_QUALITY_METRIC' : 0.8, #dimensionless
	              'POSREP_CALIBRATION_PARS' : None,
	              'display' : False}

METCAL_ANALYSIS_PARS = {
	                    'METCAL_PLATESCALE' : 0.00668, #mm per pixel
	                    'METCAL_SMALL_DIAMETER' : 1.5, #mm
	                    'METCAL_LARGE_DIAMETER' : 2.5, #mm 
	                    'METCAL_DIAMETER_TOLERANCE' : 0.1, #mm 
	                    'METCAL_GAUSS_BLUR' : 3, #pixels - MUST BE AN ODD NUMBER
	                    'METCAL_THRESHOLD' : 40,  #0-255
	                    'METCAL_QUALITY_METRIC' : 0.8, #dimensionless                            
	                    'display' : False  #will display image with contours annotated
}

METCAL_FIBRE_ANALYSIS_PARS = {
	                   'METCAL_PLATESCALE' : 0.00668, #mm per pixel
	                   'METCAL_QUALITY_METRIC' : 0.8, #dimensionless
	                   'display' : False#will display image with contours annotated
}


POSITION_REP_POSITIONS = [132, 192, 252, 312, 12, 72]

POSREP_MEASUREMENT_PARS = {
    'POSITION_REP_POSITIONS' : POSITION_REP_POSITIONS, # the rotary stage angle required to
                               # place each FPU under the positional
                               # repeatability camera
    
    'POSITION_REP_EXPOSURE_MS' : NaN,  # the exposure time in
                                       # milliseconds for a correctly
                                       # exposed image
    
    'POSITION_REP_NUMINCREMENTS' : NaN, # the number of movements made
                                     # within each positive sweep from
                                     # the starting position
    'POSITION_REP_ITERATIONS' : NaN, # the number of times each FPU
                                     # sweeps back and forth
    }


POSREP_CALIBRATION_PARS = {
    'algorithm' : 'identity',
    'coeffs' : [[NaN, NaN, NaN], [NaN, NaN, NaN], [NaN, NaN, NaN], ],
}


POSREP_EVALUATION_PARS = {
    'POSITION_REP_PASS' : NaN, # the maximum angular deviation, in
                               # degrees, from an average position of
                               # a grouping of measured points at a
                               # given nominal position which
                               # represents an acceptable FPU
}


POSVER_MEASUREMENT_PARS = {
    'POSITION_REP_POSITIONS' : POSITION_REP_POSITIONS, # the rotary stage angle required to
                               # place each FPU under the positional
                               # repeatability camera
    
    'POSITION_VER_EXPOSURE_MS' : NaN,  # the exposure time in
                                       # milliseconds for a correctly
                                       # exposed image
    
    'POSITION_VER_ITERATIONS' : NaN, # the number of times each FPU
                                     # sweeps back and forth
    }


POSVER_EVALUATION_PARS = {
    'POSITION_VER_PASS' : NaN, # the maximum angular deviation, in
                               # degrees, from an average position of
                               # a grouping of measured points at a
                               # given nominal position which
                               # represents an acceptable FPU
}



PUPALGN_MEASUREMENT_PARS = {
    'PUPIL_ALN_POSITIONS': [NaN, NaN, NaN, NaN, NaN, NaN], # the rotary stage angle required to
                                # place each FPU under the first pupil
                                # alignment fold mirror
    
    'PUPIL_ALN_LINPOSITIONS' : NaN, # the linear stage positions
                                   # required to illuminate each FPU
                                   # fibre
        
    'PUPIL_ALN_EXPOSURE_MS' : NaN, # the exposure time in milliseconds
                                # for a correctly exposed image

    }


PUPALGN_ANALYSIS_PARS = {
    'PUPALN_PLATESCALE' :0.00668, #mm per pixel
    'PUPALN_CIRCULARITY_THRESH' : 0.8, #dimensionless
    'PUPALN_NOISE_METRIC' :0,
    'PUPALN_CALIBRATION_PARS' : None,
    'display' : False
}

PUPALGN_CALIBRATION_PARS = {
    'algorithm' : 'identity',
    'coeffs' : [[NaN, NaN, NaN], [NaN, NaN, NaN], [NaN, NaN, NaN], ],
    }

PUPALGN_EVALUATION_PARS = {
    'PUPIL_ALN_PASS' : NaN, # the maximum total deviation in arcmin
                            # from the calibrated centre point which
                            # represents an acceptable FPU
}



MET_HEIGHT_MEASUREMENT_PARS = {
    'MET_HEIGHT_POSITIONS' : [268, 328, 28, 88, 148, 208], # the rotary stage angle required to place each FPU
    #                                                        in front of the metrology height camera

    'METROLOGY_HT_TARGET_EXPOSURE_MS' : NaN, # the exposure time in
                                             # milliseconds for a
                                             # correctly exposed image
                                             # of the illuminated
                                             # targets
    
    }



MET_HEIGHT_ANALYSIS_PARS =  {
    'METHT_PLATESCALE' : 0.00668, #mm per pixel
    'METHT_THRESHOLD' : 150, #0-255
    'METHT_SCAN_HEIGHT' : 2000, #pixels
    'METHT_GAUSS_BLUR' : 1, #pixels - MUST BE AN ODD NUMBER
    'METHT_STANDARD_DEV' : 0.04, #mm
    'METHT_NOISE_METRIC' : 0.25, #dimensionless
    'display' : False,
}

