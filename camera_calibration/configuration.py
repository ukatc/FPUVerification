import attr
import cv2 as cv
import math
import numpy as np


@attr.s
class Corners:
    """
    Stores (X, Y) pairs for corners of a rectangle in an image
    """
    top_left = attr.ib()
    top_right = attr.ib()
    bottom_left = attr.ib()
    bottom_right = attr.ib()


@attr.s
class Config:
    """
    Camera calibration properties for a fixed camera looking at a given plane
    """
    distorted_camera_matrix = attr.ib(type=np.ndarray, default=None)
    distortion_coefficients = attr.ib(type=np.ndarray, default=None)
    undistorted_camera_matrix = attr.ib(type=np.ndarray, default=None)
    homography_matrix = attr.ib(type=np.ndarray, default=None)
    grid_image_corners = attr.ib(type=Corners, default=None)
    grid_space_corners = attr.ib(type=Corners, default=None)

    @staticmethod
    def generate(
            chessboard_path, chess_rows, chess_cols,
            dot_grid_path, dot_detector, dot_rows, dot_cols, dot_grid_width, dot_grid_height
    ):
        """
        Generate a calibration configuration object for a camera using a pair of chessboard and dot grid images
        :param chessboard_path: The path to a chessboard image taken by the camera
        :param chess_rows: The number of rows of square-intersection points in the grid
        :param chess_cols: The number of columns of square-intersection points in the grid
        :param dot_grid_path: The path to an image of a grid of dots taken by the camera
        :param dot_detector: An openCV dot detector able to detect all the dots in the given image
        :param dot_rows: The number of rows in the dot grid
        :param dot_cols: The number of columns in the dot grid
        :param dot_grid_width: The width of the dot grid, measured from dot centers
        :param dot_grid_height: The height of the dot grid, measured from dot centers
        :return: A pair indicating if the configuration object was fully constructed, and the configuration object
        """
        config = Config()

        chessboard = cv.imread(chessboard_path)
        gray_chessboard = cv.cvtColor(chessboard, cv.COLOR_BGR2GRAY)
        found, corners = cv.findChessboardCorners(gray_chessboard, (chess_rows, chess_cols))
        if not found:
            return False, config

        objp = np.zeros((chess_cols * chess_rows, 3), np.float32)
        objp[:, :2] = np.mgrid[0:chess_rows*5:5, 0:chess_cols*5:5].T.reshape(-1, 2)
        objpoints = [objp]
        imgpoints = [corners]

        h, w = chessboard.shape[:2]
        calibrated, camera_matrix, distortion_coefficients, _, _ = cv.calibrateCamera(objpoints, imgpoints, (w, h), None, None)

        if not calibrated:
            return False, config

        config.distorted_camera_matrix = camera_matrix
        config.distortion_coefficients = distortion_coefficients

        new_camera_matrix, _ = cv.getOptimalNewCameraMatrix(camera_matrix, distortion_coefficients, (w, h), 1, (w, h))

        config.undistorted_camera_matrix = new_camera_matrix

        dots = cv.imread(dot_grid_path)
        delensed = cv.undistort(dots, camera_matrix, distortion_coefficients, None, new_camera_matrix)
        found, grid = cv.findCirclesGrid(
            delensed,
            (dot_cols, dot_rows),
            cv.CALIB_CB_SYMMETRIC_GRID + cv.CALIB_CB_CLUSTERING,
            dot_detector,
            cv.CirclesGridFinderParameters()
        )

        if not found:
            return False, config

        bottom_right = grid[0, 0]
        bottom_left = grid[dot_cols - 1, 0]
        top_left = grid[-1, 0]
        top_right = grid[-dot_cols, 0]

        def distance(p1, p2):
            return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

        border = 50
        grid_width = max(distance(top_left, top_right),
                         distance(bottom_left, bottom_right))
        grid_height = max(distance(top_left, bottom_left),
                          distance(top_right, bottom_right))
        point_spacing = math.ceil(max(grid_width / (dot_cols - 1),
                                      grid_height / (dot_rows - 1)))
        grid_width = point_spacing * (dot_cols - 1)
        grid_height = point_spacing * (dot_rows - 1)

        target_corners = np.array([
            [border, border],  # top left
            [grid_width + border, border],  # top right
            [border, grid_height + border],  # bottom left
            [grid_width + border, grid_height + border],  # bottom right
        ])

        target_points = np.zeros((dot_rows * dot_cols, 2), np.float32)
        # measuring from the bottom left, initially going along rows, to match the detected dot grid
        for row in range(dot_rows):
            for col in range(dot_cols):
                target_points[row * dot_cols + col, :2] = ((border + ((dot_cols - (1+col)) * point_spacing)),
                                                           (border + ((dot_rows - (1+row)) * point_spacing)))

        grid_points = np.array([dot[0] for dot in grid])

        config.homography_matrix, _ = cv.findHomography(grid_points, target_points)
        config.grid_image_corners = Corners(*target_corners)
        config.grid_space_corners = Corners((0, 0), (dot_grid_width, 0), (0, dot_grid_height), (dot_grid_width, dot_grid_height))

        return True, config
