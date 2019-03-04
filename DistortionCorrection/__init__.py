from __future__ import print_function, division,  absolute_import

from ImageAnalysisFuncs.base import ImageAnalysisError

class CorrectionError(ImageAnalysisError):
    pass

def correct(image, calibration_pars=None):
    if (calibration_pars == None) or (
            calibration_pars['algorithm'] == 'identity'):
        return image

    #possible commands for camera calibration
    #newcameramtx, roi=cv2.getOptimalNewCameraMatrix(calibration_pars['CAMERA_MATRIX'],
    #    calibration_pars['DISTORTION_COEFFICIENTS'],(w,h),1,(w,h))	
    #mapx,mapy = cv2.initUndistortRectifyMap(calibration_pars['CAMERA_MATRIX'],
    #    calibration_pars['CAMERA_MATRIX'],None,newcameramtx,(w,h),5)
    #image_corr = cv2.remap(image,mapx,mapy,cv2.INTER_LINEAR)
    
    raise CorrectionError("unknown algorithm")

    
                             
