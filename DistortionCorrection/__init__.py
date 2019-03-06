from __future__ import print_function, division,  absolute_import

from ImageAnalysisFuncs.base import ImageAnalysisError

class CorrectionError(ImageAnalysisError):
    pass

def correct(x, y, calibration_pars=None):
    if (calibration_pars == None) or (
            calibration_pars['algorithm'] == 'identity'):
        return x, y
    elif calibration_pars['algorithm'] == 'scale':
        return x * calibration_pars['scale_factor'], y * calibration_pars['scale_factor']
    
    raise CorrectionError("unknown algorithm")

    
                             
