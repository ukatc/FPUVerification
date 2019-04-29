import camera_calibration as calib
import numpy as np
import os

# Chessboard image distcor_004.bmp, full grid homography
#   average deviation: 0.364139029306mm
#   max deviation:     0.832382619819mm
# this data was generated with the script "search_for_best_pupil_cinfig.py", with
# the input image in $IMAGE_ROOT_FOLDER/../calibration/images/pup-algn/distcor_004.bmp

from_constructor = calib.Config(
    distorted_camera_matrix=np.array(
        [
            [4681.74594217, 0.0, 980.69946863],
            [0.0, 5357.78011109, 604.19718367],
            [0.0, 0.0, 1.0],
        ]
    ),
    distortion_coefficients=np.array(
        [[-1.85381058, -43.40650075, 0.00164297, -0.05988727, 1313.59256105]]
    ),
    undistorted_camera_matrix=np.array(
        [
            [4452.88330078, 0.0, 945.37500454],
            [0.0, 4944.70849609, 604.61159019],
            [0.0, 0.0, 1.0],
        ]
    ),
    homography_matrix=np.array(
        [
            [1.09721761, 0.0749314, -458.46636981],
            [-0.01266892, 1.22193234, -37.49456483],
            [-0.00000743, 0.00012395, 1.0],
        ]
    ),
    grid_image_corners=calib.Corners(
        top_left=np.array([200.0, 200.0]),
        top_right=np.array([676.0, 200.0]),
        bottom_left=np.array([200.0, 880.0]),
        bottom_right=np.array([676.0, 880.0]),
    ),
    grid_space_corners=calib.Corners(
        top_left=np.array([0.0, 0.0], dtype=np.float32),
        top_right=np.array([318.83493, 0.0], dtype=np.float32),
        bottom_left=np.array([0.0, 455.4785], dtype=np.float32),
        bottom_right=np.array([318.83493, 455.4785], dtype=np.float32),
    ),
)

from_dict = calib.Config.from_dict(
    {
        "undistorted_camera_matrix": [
            [4452.88330078125, 0.0, 945.3750045370543],
            [0.0, 4944.70849609375, 604.6115901880075],
            [0.0, 0.0, 1.0],
        ],
        "distorted_camera_matrix": [
            [4681.745942174919, 0.0, 980.6994686335167],
            [0.0, 5357.780111091218, 604.197183671316],
            [0.0, 0.0, 1.0],
        ],
        "grid_image_corners": {
            "top_right": [676.0, 200.0],
            "bottom_left": [200.0, 880.0],
            "bottom_right": [676.0, 880.0],
            "top_left": [200.0, 200.0],
        },
        "distortion_coefficients": [
            [
                -1.8538105783847776,
                -43.406500749633246,
                0.0016429671626481382,
                -0.059887270902587206,
                1313.592561053839,
            ]
        ],
        "homography_matrix": [
            [1.09721760688824, 0.07493140087449279, -458.4663698084087],
            [-0.012668924740513583, 1.2219323449217627, -37.49456482661192],
            [-7.42502951473456e-06, 0.00012395433684126206, 1.0],
        ],
        "grid_space_corners": {
            "top_right": [318.8349304199219, 0.0],
            "bottom_left": [0.0, 455.4784851074219],
            "bottom_right": [318.8349304199219, 455.4784851074219],
            "top_left": [0.0, 0.0],
        },
    }
)

# The coefficients are saved with one extra
# level of indirection, which would allow it to correct
# or improve calibrations for images which were
# gathered earlier. This first file holds the coefficients,
# and the second file points to that file.
#
# Within the verification software, the name of the second file is
# passed as the camera calibration for each image to the image
# analysis script.

IMAGE_ROOT_FOLDER = os.environ.get("IMAGE_ROOT_FOLDER", "/moonsdata/verification/images")

cal_file_name = os.path.join(
    IMAGE_ROOT_FOLDER,
    '..',
    "calibration",
    "cal_al_20190429_chessboard.npz"
)

print("saving coefficients in %s" % cal_file_name)

with open(cal_file_name, "wt") as coef_file:
    from_dict.save(coef_file)


mapping = """# file: calibration/mapping/pup-aln-2019-04-10.cfg
{
    'algorithm' : "al/20190429/chessboard",
    'calibration_config_file' : "calibration/cal_al_20190429_chessboard.npz",
#    'dot_grid_image_path' : "",
    'chessboard_image_path' : "",
}
"""

map_file_name = os.path.join(
    IMAGE_ROOT_FOLDER,
    '..',
    "calibration",
    "mapping",
    "pup-aln-2019-04-10.cfg"
)

print("saving mapping in %s" % map_file_name)

with open(map_file_name, "wt") as map_file:
    map_file.writelines(mapping)
