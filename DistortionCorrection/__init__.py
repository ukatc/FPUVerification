from __future__ import print_function, division,  absolute_import

from ImageAnalysisFuncs.base import ImageAnalysisError

class CorrectionError(ImageAnalysisError):
    pass

def correct(image, calibration_pars=None):
    if (calibration_pars == None) or (
            calibration_pars['algorithm'] == 'identity'):
        return image
    raise CorrectionError("unknown algorithm")

    
                             
