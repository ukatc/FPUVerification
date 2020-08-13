# -*- coding: utf-8 -*-
"""

Module to evaluate positional verification.

"""
from __future__ import division, print_function

import math
from math import pi
import numpy as np
import warnings
import logging

from Gearbox.gear_correction import angle_to_point, cartesian_blob_position, \
                                    elliptical_distortion, leastsq_circle, fit_offsets, \
                                    points_to_offset, datum_to_camera_offset, datum_to_beta0
from vfr.evaluation.measures import get_errors, get_measures, get_weighted_coordinates

from vfr.conf import POS_REP_EVALUATION_PARS, POS_VER_EVALUATION_PARS, \
                     GRAPHICAL_DIAGNOSTICS, MIN_POINTS_FOR_CIRCLE_FIT

# Plot the alpha circles used to calibrate FPU centre
PLOT_ALPHA_CIRCLES = False
PLOT_BETA_CIRCLES = False
PLOT_OFFSET_CIRCLES = False

# Show the location of uncalibrated points on the diagnostic plots?
SHOW_UNCALIBRATED_POINTS = False

# Plotting library used for diagnostics.
if GRAPHICAL_DIAGNOSTICS:
    try:
        import moc_plotting as plotting
    except ImportError:
        GRAPHICAL_DIAGNOSTICS = False


POS_VER_ALGORITHM_VERSION = (1, 0, 0)

#
# Modify these flags to control how the algorithm works.
#
# Apply an elliptical distortion to the *measured* points!
# Set False to implement the SMB change or True for old behaviour.
# TODO: Eventually remove this option altogether.
APPLY_ELLIPTICAL_DISTORTION = False   # Recommended setting False


def evaluate_positional_verification(
    dict_of_coords,            # Dictionary of coordinates, as defined below.
    list_of_datum_result=None, # List of datum positions (x,y) in chronological order (optional)    
    pars=None,                 # Configuration parameters?
    x_center=None,             # X centre of alpha axis
    y_center=None,             # Y centre of alpha axis
    R_alpha=None,              # Calibrated radius of alpha circle
    R_beta_midpoint=None,      # Calibrated radius of beta circle
    camera_offset_rad=None,    # Calibrated camera angle offset
    beta0_rad=None,            # Calibrated beta angle offset
    coeffs=None,               # Gearbox calibration coefficients
    BLOB_WEIGHT_FACTOR=None,   # Weighting factor between large and small metrology blobs.
    plot=True,                 # Not used
    **kwargs
):
    """Takes a dictionary. The keys of the dictionary are the idx, alpha_nom,
    beta_nom parameters of the positional repeteability measurement.

    The values of the dictionary are a 6-tuple
    (x_measured_1, y_measured_1, qual1, x_measured_2, y_measured_2, qual2).

    Here, (alpha_nom, beta_nom) are the angle coordinates given by the
    motor step counts (measured in degrees), and (x_measured,
    y_measured) are the cartesian values of the large (index 1) and
    the small (index 2) blob target coordinates measured from the
    images taken.


    The units are in degrees (for alpha_nom and beta_nom) and pixel
    units (for x_measured and y_measured). The y axis of the pixel
    units is always positive with the origiin in the upper left corner
    (that is, it is pointing in the inverse direction compared to the
    y axis of a Cartesian system).

    The returned value are the repeatability measures in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """
    
    logger = logging.getLogger(__name__)
    
    expected_points = {} # arm coordinates + index vs. expected Cartesian position
    measured_points = {} # arm coordinates + index vs. actual Cartesian position
    error_vectors = {} # arm coordinates + index vs. delta (expected - measured)
    error_by_angle = {} # arm coordinates + index vs. magnitude of error vector

    # Get measured circle center point from alpha arm calibration
    #
    # FPU centre and orientation has changed because of the turntable movement, so it
    # needs to be rederived from the images taken. The data set is searched for
    # circles where the alpha angle varies and the beta angle remains fixed.
    # The average of the centres of these circles is defined to be the FPU centre.

    logger.debug("Locating alpha circles within the data.")
    circle_points = {}
    alpha_nom_rad_array = {}
    beta_nom_rad_array = {}
    for coords, blob_pair in dict_of_coords.items():
        #print("-------------")
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        xcirc, ycirc = cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)
        alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
        #print("idx:", idx, "nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg), "(deg)")
        #print("ixd=%d, beta=%f (deg), blob_pair=%s, circle_point=(%f,%f)." % \
        #    (idx, beta_nom_deg, str(blob_pair), xcirc, ycirc))
        if beta_nom_deg in circle_points:
            circle_points[beta_nom_deg].append((xcirc, ycirc))
            alpha_nom_rad_array[beta_nom_deg].append(alpha_nom_rad)
            beta_nom_rad_array[beta_nom_deg].append(beta_nom_rad)
        else:
            circle_points[beta_nom_deg] = [(xcirc, ycirc)]
            alpha_nom_rad_array[beta_nom_deg] = [alpha_nom_rad]
            beta_nom_rad_array[beta_nom_deg] = [beta_nom_rad]

    for bkey in list(circle_points.keys()):
        # Only fit circles with a sufficient number of points
        npoints = len(circle_points[bkey])
        if npoints < MIN_POINTS_FOR_CIRCLE_FIT:
           #print("Only %d points for beta=%s. Deleting." % (npoints, str(bkey)))
           del circle_points[bkey]
           del alpha_nom_rad_array[bkey]
           del beta_nom_rad_array[bkey]
        #else:
        #   print("%d points for beta=%s. Keeping." % (npoints, str(bkey)))

    logger.info("Deriving new alpha axis center.")
    circles_alpha = {}
    xpts = []
    ypts = []
    npts = 0
    for bkey in list(circle_points.keys()):
        x_s, y_s = np.array(circle_points[bkey]).T
        xc, yc, radius, psi, stretch, _ = leastsq_circle(x_s, y_s)
        if stretch > 1.0:
            stretch = 1.0/stretch
            psi += pi/2.0
        logger.debug("Fitted centre for beta {:.3f} is {:.5f},{:.5f} (mm)".format(bkey, xc, yc))
        logger.debug("Radius = {:.5f} (mm), psi={:.4f} (deg), stretch={}".format(radius, np.rad2deg(psi), stretch))

        xcom = np.mean(x_s)
        ycom = np.mean(y_s)
        logger.debug("Centre of mass for for beta {:.3f} is {:.5f},{:.5f} (mm). Difference {:.5f},{:.5f}.".format(
            bkey, xcom, ycom, xcom-xc, ycom-yc))

        # Only accept the fit if the points sample the circle well and are
        # not skewed to one side.
        if (abs(xcom-xc) < POS_REP_EVALUATION_PARS.MAX_CENTRE_SHIFT) and \
           (abs(ycom-yc) < POS_REP_EVALUATION_PARS.MAX_CENTRE_SHIFT):
            # Circle accepted
            #print("Circle fit accepted.")
            xpts.append(xc)
            ypts.append(yc)
            npts += 1
            
            # Create a Circle object
            circles_alpha[bkey] = {
                     'x_s2': x_s,
                     'y_s2': y_s,
                     'xc': xc,
                     'yc': yc,
                     'stretch': stretch,
                     'psi': psi,
                     'R': radius,
                     'alpha_nominal_rad': alpha_nom_rad_array[bkey],
                     'beta_nominal_rad' : beta_nom_rad_array[bkey]
                   }            
        #else:
        #    print("Circle fit rejected.")

    # Find the mean centre
    if npts > 0:
        if npts == 1:
            xmean = xpts[0]
            ymean = ypts[0]
        else:
            xpts = np.asarray(xpts)
            ypts = np.asarray(ypts)
            xmean = np.mean(xpts)
            ymean = np.mean(ypts)
        P0 = np.array([xmean, ymean])
        logger.info("P0 = {:.5f},{:.5f} (from {} circles) compared with (x_center,y_center) = {:.5f},{:.5f} (mm)".format(
            xmean, ymean, npts, x_center, y_center))
        logger.info("R = {:.4f} compared with R_alpha={:.4f} R_beta_midpoint={:.4f} (mm)".format(
            radius, R_alpha, R_beta_midpoint))
        if npts > 2:
           logger.info("Standard deviation of circle centres = {:.5f},{:.5f} (mm)".format(
               np.std(xpts), np.std(ypts)))
    else:
        logger.warning("Unsufficient circle points to fit the alpha centre! Original centre assumed.")
        P0 = np.array([x_center, y_center])
        logger.info("P0 = (x_center,y_center) = {:.5f}, {:.5f} (mm)".format(x_center, y_center))

    if GRAPHICAL_DIAGNOSTICS and PLOT_ALPHA_CIRCLES:
        # Plot the alpha circles.
        title = "evaluate_positional_verification: Alpha circle points for centre fitting"
        title += "\n(each colour represents different beta angle)"
        linefmts = ['b.', 'y.', 'm.', 'c.', 'r.', 'g.',  'k.']
        ifmt = 0
        for bkey in list(circle_points.keys()):
            acx = []
            acy = []
            for cp in circle_points[bkey]:
                acx.append( cp[0] )
                acy.append( cp[1] )
            linefmt = linefmts[ifmt]
            ifmt = (ifmt + 1) % len(linefmts)
            plotaxis = plotting.plot_xy( acx, acy, title=title,
                          xlabel='X (mm)', ylabel='Y (mm)',
                          linefmt=linefmt, linestyle=' ', equal_aspect=True, showplot=False )
            cen_x = [x_center, xmean]
            cen_y = [y_center, ymean]
        plotting.plot_xy( cen_x, cen_y, title=None,
                  xlabel=None, ylabel=None,
                  linefmt='r+', linestyle=' ', equal_aspect=True,
                  plotaxis=plotaxis, showplot=True )

    # NOTE: If the remaining points are used to make a "circle_beta" data structure and all
    # the points used to derive a new beta0 angle, the results get worse.

    if (POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM == "BETA"):

        logger.debug("Locating beta circles within the data.")
        circle_points = {}
        alpha_nom_rad_array = {}
        beta_nom_rad_array = {}
        for coords, blob_pair in dict_of_coords.items():
            #print("-------------")
            (idx, alpha_nom_deg, beta_nom_deg) = coords
            xcirc, ycirc = cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)
            alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
            #print("idx:", idx, "nominal: (alpha, beta) = ", (alpha_nom_deg, beta_nom_deg), "(deg)")
            #print("ixd=%d, beta=%f (deg), blob_pair=%s, circle_point=(%f,%f)." % \
            #    (idx, beta_nom_deg, str(blob_pair), xcirc, ycirc))
            if alpha_nom_deg in circle_points:
                circle_points[alpha_nom_deg].append((xcirc, ycirc))
                alpha_nom_rad_array[alpha_nom_deg].append(alpha_nom_rad)
                beta_nom_rad_array[alpha_nom_deg].append(beta_nom_rad)
            else:
                circle_points[alpha_nom_deg] = [(xcirc, ycirc)]
                alpha_nom_rad_array[alpha_nom_deg] = [alpha_nom_rad]
                beta_nom_rad_array[alpha_nom_deg] = [beta_nom_rad]
    
        for akey in list(circle_points.keys()):
            # Only fit circles with a sufficient number of points
            npoints = len(circle_points[akey])
            if npoints < MIN_POINTS_FOR_CIRCLE_FIT:
               #print("Only %d points for alpha=%s. Deleting." % (npoints, str(bkey)))
               del circle_points[akey]
               del alpha_nom_rad_array[akey]
               del beta_nom_rad_array[akey]
            #else:
            #   print("%d points for alpha=%s. Keeping." % (npoints, str(bkey)))
    
        logger.info("Fitting circles to find beta axis centers.")
        circles_beta = {}
        co_total = 0.0
        nbpts = 0
        for akey in list(circle_points.keys()):
            x_s, y_s = np.array(circle_points[akey]).T
            xc, yc, radius, psi, stretch, _ = leastsq_circle(x_s, y_s)
            if stretch > 1.0:
                stretch = 1.0/stretch
                psi += pi/2.0
            logger.debug("Fitted centre for alpha {:.3f} is {:.5f},{:.5f} (mm)".format(akey, xc, yc))
            logger.debug("Radius = {:.5f} (mm), psi={:.4f} (deg), stretch={}".format(radius, np.rad2deg(psi), stretch))
    
            xcom = np.mean(x_s)
            ycom = np.mean(y_s)
            logger.debug("Centre of mass for for alpha {:.3f} is {:.5f},{:.5f} (mm). Difference {:.5f},{:.5f}.".format(
                akey, xcom, ycom, xcom-xc, ycom-yc))
    
            # Only accept the fit if the points sample the circle well and are
            # not skewed to one side.
            # NOTE: The beta circle test is less strict than the alpha circle test.
            if (abs(xcom-xc) < POS_REP_EVALUATION_PARS.MAX_CENTRE_SHIFT*2.0) and \
               (abs(ycom-yc) < POS_REP_EVALUATION_PARS.MAX_CENTRE_SHIFT*2.0):
                # Circle accepted
                #print("Circle fit accepted.")
     
                # Estimate the camera offset from the location of the beta circle centre.
                Pcb = np.array([xc, yc])
                alpha_mean_rad = np.mean(alpha_nom_rad_array[akey]) # float(akey)?
                offset_estimate = points_to_offset( alpha_mean_rad, P0, Pcb )
                strg = "alpha fixpoint %f (deg): mean alpha=%f (deg). " % (akey, np.rad2deg(alpha_mean_rad))
                strg += "camera offset estimate from beta centre=%f (deg) compared with %f (deg)" % \
                    (np.rad2deg(offset_estimate), np.rad2deg(camera_offset_rad))
                logger.debug(strg)
                if abs(offset_estimate - camera_offset_rad) < POS_REP_EVALUATION_PARS.MAX_OFFSET_SHIFT_RAD:
                    co_total += offset_estimate
                    nbpts += 1
            #else:
            #    print("Circle fit rejected.")
            
        if nbpts > 0:
            camera_offset_new = co_total/float(nbpts)
            logger.info("Mean camera offset from beta axes from %d circles: %f (rad) = %f (deg)" % \
                        (nbpts, camera_offset_new, np.rad2deg(camera_offset_new)))
        else:
            logger.warn("Insufficient good beta circles to estimate the camera offset. Alpha circles will be used instead.")
            POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM = "ALPHA"

        if GRAPHICAL_DIAGNOSTICS and PLOT_BETA_CIRCLES:
            # Plot the alpha circles.
            title = "evaluate_positional_verification: Beta circle points for camera offset estimate"
            title += "\n(each colour represents different alpha angle)"
            linefmts = ['b.', 'y.', 'm.', 'c.', 'r.', 'g.',  'k.']
            ifmt = 0
            for akey in list(circle_points.keys()):
                acx = []
                acy = []
                for cp in circle_points[akey]:
                    acx.append( cp[0] )
                    acy.append( cp[1] )
                linefmt = linefmts[ifmt]
                ifmt = (ifmt + 1) % len(linefmts)
                plotaxis = plotting.plot_xy( acx, acy, title=title,
                              xlabel='X (mm)', ylabel='Y (mm)',
                              linefmt=linefmt, linestyle=' ', equal_aspect=True, showplot=False )
                cen_x = [x_center, xmean]
                cen_y = [y_center, ymean]
            plotting.plot_xy( cen_x, cen_y, title=None,
                      xlabel=None, ylabel=None,
                      linefmt='r+', linestyle=' ', equal_aspect=True,
                      plotaxis=plotaxis, showplot=True )

    if list_of_datum_result is not None and len(list_of_datum_result) > 0:
        logger.info("%d datum measurements available." % len(list_of_datum_result))
        datum_available = True
        
        # Report the variation in the datum results
        ndatum = len(list_of_datum_result)
        rdiff = 0.0
        if ndatum > 1:
            rdiffsq = 0.0
            for ii in range(1, ndatum):
                xdiff = list_of_datum_result[ii][0] - list_of_datum_result[ii-1][0]
                ydiff = list_of_datum_result[ii][1] - list_of_datum_result[ii-1][1]
                rdiffsq += xdiff*xdiff + xdiff*ydiff
            rdiff = math.sqrt(rdiffsq/float(ndatum-1))
        else:
            xdiff = list_of_datum_result[1][0] - list_of_datum_result[0][0]
            ydiff = list_of_datum_result[1][1] - list_of_datum_result[0][1]
            rdiff = math.sqrt( xdiff*xdiff + ydiff*ydiff)
        logger.info("NOTE: Datum measurements shifted by an RMS of %f mm (%.1f micron)." %
                    (rdiff, rdiff*1000.0))
    else:
        datum_available = False

    if (POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM == "DATUM") and datum_available:
        # Estimate the camera offset from the datum measurement.
        logger.info("Deriving new camera offset (to correct turntable tilt) from datum measurements.")
        camera_offset_total = 0.0
        ngood = 0
        for Pdatum in list_of_datum_result:
            camera_offset_estimate = datum_to_camera_offset( Pdatum, P0, R_alpha, R_beta_midpoint,
                                             beta0_rad )
            logger.debug("Datum measurement at {} suggests camera_offset {:.4f} compared with {:.4f} (deg)".format(
                Pdatum, np.rad2deg(camera_offset_estimate), np.rad2deg(camera_offset_rad)))
            if abs(camera_offset_estimate - camera_offset_rad) < POS_REP_EVALUATION_PARS.MAX_OFFSET_SHIFT_RAD:
                ngood += 1
                camera_offset_total += camera_offset_estimate
 
        if ngood > 0:
            camera_offset_new = camera_offset_total/float(ngood)
            logger.info("New mean camera offset from datum= {:.4f} compared with {:.4f} (deg)".format(
                np.rad2deg(camera_offset_new), np.rad2deg(camera_offset_rad)))
        else:
            logger.warn("Unsufficient good datum measurements to derive camera offset. Alpha circles will be used instead.")
            datum_available = False
            POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM = "ALPHA"
    elif not datum_available:
        logger.warn("No datum measurements available to derive camera offset. Alpha circles will be used instead.")
        POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM = "ALPHA"

    if (POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM == "ALPHA"):
        # Find the best fit for the camera offset
        logger.info("Deriving new camera offset (to correct turntable tilt) by fitting.")
        camera_offset_total = 0.0
        ncams = 0
        for bkey in list(circles_alpha.keys()):
            #print("circle_alpha=", circle_alpha)
            camera_offset_this, beta0_new = fit_offsets(
                                   circles_alpha[bkey],                  # Fit alpha circle only
                                   circle_beta=None,                     #
                                   P0=P0,                                # Use new alpha axis centre
                                   R_alpha=R_alpha,                      # Previous calibrated radius of alpha circle
                                   R_beta_midpoint=R_beta_midpoint,      # Previous calibrated radius of beta circle
                                   camera_offset_start=camera_offset_rad,# Start with previous camera angle offset
                                   beta0_start=beta0_rad,                # Fixed beta0
                                   verbose=False,
                                   plot=PLOT_OFFSET_CIRCLES
                              )
            logger.debug("beta={}. Fitted camera offset= {:.4f} compared with {:.4f} (deg)".format(
                bkey, np.rad2deg(camera_offset_this), np.rad2deg(camera_offset_rad)))
            logger.debug("New beta0= {:.4f} (ignored) compared with {:.4f} (deg)".format(
                np.rad2deg(beta0_new), np.rad2deg(beta0_rad)))
            if abs(camera_offset_this - camera_offset_rad) < POS_REP_EVALUATION_PARS.MAX_OFFSET_SHIFT_RAD:
                camera_offset_total += camera_offset_this
                ncams += 1
        if ncams > 0:
            camera_offset_new = camera_offset_total / float(ncams)
            logger.info("New mean camera offset from fit= {:.4f} compared with {:.4f} (deg)".format(
                np.rad2deg(camera_offset_new), np.rad2deg(camera_offset_rad)))
        else:
            logger.warn("Unsufficient good fits to derive camera offset. Original value retained.")
            camera_offset_new = camera_offset_rad
    elif POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM == "ORIGINAL":
        logger.info("Original value of camera offset used = {:.4f} (deg).".format(
                np.rad2deg(camera_offset_rad)))
        camera_offset_new = camera_offset_rad

    if datum_available:
        if POS_VER_EVALUATION_PARS.RECALIBRATE_BETA0: # --- Recalibrate beta0 using datum?
            if POS_VER_EVALUATION_PARS.CAMERA_OFFSET_FROM == "DATUM":
                logger.warning("camera_offset and beta0 cannot both be derived from datum.")
            beta0_total = 0.0
            for Pdatum in list_of_datum_result:
                beta0_estimate = datum_to_beta0( Pdatum, P0, R_alpha, R_beta_midpoint,
                                                 camera_offset_new )
                beta0_total += beta0_estimate
                logger.debug("Datum measurement at %s suggests beta0 = %f (rad) = %f (deg)" % \
                            (str(Pdatum), beta0_estimate, np.rad2deg(beta0_estimate)))
            beta0_rad = beta0_total/float(ndatum)
            logger.info("Mean beta0 from datum (1): %f (rad) = %f (deg)" % \
                        (beta0_rad, np.rad2deg(beta0_rad)))


    # Go back to the start and read the input data from the beginning.
    uncalibrated_points = {} # arm coordinates + index vs. uncalibrated Cartesian position
    expected_points = {}     # arm coordinates + index vs. expected Cartesian position
    measured_points = {}     # arm coordinates + index vs. actual Cartesian position

    # Now extract all the points from the dictionary.
    for coords, blob_pair in dict_of_coords.items():
        # get nominal coordinates
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        logger.debug("idx: {} nominal: (alpha, beta) = {},{} (deg)".format(
            idx, alpha_nom_deg, beta_nom_deg))
        alpha_nom_rad, beta_nom_rad = np.deg2rad(alpha_nom_deg), np.deg2rad(beta_nom_deg)
        expected_pos = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            P0=P0,                               # Use the new alpha axis centre
            #coeffs=coeffs,
            coeffs=None,                         # inactive because already corrected
            R_alpha=R_alpha,                     # Use the previous calibrated alpha radius
            R_beta_midpoint=R_beta_midpoint,     # Use the previous calibrated beta radius
            camera_offset_rad=camera_offset_new, # Use the new camera offset
            beta0_rad=beta0_rad,                 # Stick with the original beta0
            broadcast=False,
            verbose=True
        )
        if SHOW_UNCALIBRATED_POINTS:
            # Apply the gearbox correction to determine where the uncalibrated points
            # would be.
            uncalibrated_pos = angle_to_point(
                alpha_nom_rad,
                beta_nom_rad,
                P0=P0,                               # Use the new alpha axis centre
                coeffs=coeffs,
                inverse=False,                       # Apply forwards transform
                #inverse=True,                        # Apply inverse transform
                R_alpha=R_alpha,                     # Use the previous calibrated alpha radius
                R_beta_midpoint=R_beta_midpoint,     # Use the previous calibrated beta radius
                camera_offset_rad=camera_offset_new, # Use the new camera offset
                beta0_rad=beta0_rad,                 # Stick with the original beta0
                broadcast=False,
                verbose=True
            )

            uncalibrated_points[coords] = uncalibrated_pos
            logger.debug("uncalibrated_pos = {}".format( uncalibrated_pos ))

        expected_points[coords] = expected_pos
        logger.debug("expected_pos = {}".format( expected_pos ))

        # Convert blob pair image coordinates to
        # Cartesian coordinates of mid point.
        #
        # Attention: This function flips the y axis, as in the gearbox calibration
        xmd, ymd = cartesian_blob_position(blob_pair, weight_factor=BLOB_WEIGHT_FACTOR)

        # apply (small) elliptical distortion correction as in the
        # gearbox calibration computation for the alpha arm.
        #
        # NOTE FROM JN: This is sloppy and only a stop-gap: we probably need
        # to model that the FPU metrology targets are really moving on
        # a sphere, not on a tilted plane. The circles for alpha and
        # beta calibration measurements are just two subsets of that
        # sphere, but the verification measurement can select any
        # point on it.
        if APPLY_ELLIPTICAL_DISTORTION:
           xm, ym = elliptical_distortion(xmd, ymd, xc, yc, psi, stretch)
        else:
           xm, ym = xmd, ymd

        measured_pos = np.array([xm, ym], dtype=float)
        measured_points[coords] = measured_pos

        logger.debug("measured_pos = {}".format(measured_pos))
        error_vec = measured_pos - expected_pos
        error_vectors[coords] = error_vec
        error_vec_norm = np.linalg.norm(measured_pos - expected_pos)
        error_vec_norm_um = 1000 * error_vec_norm

        if ( error_vec_norm_um > 100.0 ):
           errlabel = "!!"
        elif ( error_vec_norm_um > 50.0 ):
           errlabel = "**"
        else:
           errlabel = ""
        logger.debug("error = %s, magnitude = %.5f (mm) = %.1f (um) %s" % \
            ( str(error_vec), error_vec_norm, error_vec_norm_um, errlabel ))
        error_by_angle[coords] = error_vec_norm

    if GRAPHICAL_DIAGNOSTICS:
        EXAGGERATION = 20.0
        uncalibrated_x =[]
        uncalibrated_y = []
        expected_x =[]
        expected_y = []
        measured_x = []
        measured_y = []
        vectors_x = []
        vectors_y = []
        for key in measured_points.keys():
           #print("Looking up expected and measured points for", key)
           if SHOW_UNCALIBRATED_POINTS:
              (ux, uy) = uncalibrated_points[key]
           (ex, ey) = expected_points[key]
           (mx, my) = measured_points[key]
           if EXAGGERATION > 1.0:
              if SHOW_UNCALIBRATED_POINTS:
                  ux = ex + (ux-ex) * EXAGGERATION
                  uy = ey + (uy-ey) * EXAGGERATION
              mx = ex + (mx-ex) * EXAGGERATION
              my = ey + (my-ey) * EXAGGERATION
           #print("   measured=", (mx, my), "expected=", (ex, ey))
           if SHOW_UNCALIBRATED_POINTS:
               uncalibrated_x.append(ux)
               uncalibrated_y.append(uy)
           expected_x.append(ex)
           expected_y.append(ey)
           measured_x.append(mx)
           measured_y.append(my)
           if SHOW_UNCALIBRATED_POINTS:
              vectors_x.append( [ux, ex, mx] )
              vectors_y.append( [uy, ey, my] )
           else:
              vectors_x.append( [ex, mx] )
              vectors_y.append( [ey, my] )
        title = "evaluate_positional_verification: Measured (blue), expected (red) "
        if SHOW_UNCALIBRATED_POINTS:
           title += "and uncalibrated (green) "
        title += "points overlaid.\n"
        title += "cam_offset=%.3f (deg) " % np.rad2deg(camera_offset_new)
        title += "beta0=%.3f (deg)." % np.rad2deg(beta0_rad)
        if EXAGGERATION > 1.0:
           title += "\nErrors exaggerated by a factor of %f." % EXAGGERATION
        plotaxis = plotting.plot_xy( expected_x, expected_y, title=title,
                          xlabel='X (mm)', ylabel='Y (mm)',
                          linefmt='b.', linestyle='', equal_aspect=True, showplot=False )
        for vec_x, vec_y in zip(vectors_x, vectors_y):
            plotaxis = plotting.plot_xy( vec_x, vec_y,
                              linefmt='k', linestyle='-', equal_aspect=True, showplot=False )
        if SHOW_UNCALIBRATED_POINTS:
           plotaxis = plotting.plot_xy( uncalibrated_x, uncalibrated_y, title=None,
                             xlabel=None, ylabel=None,
                             linefmt='g.', linestyle=' ', equal_aspect=True,
                             plotaxis=plotaxis, showplot=False )
        plotting.plot_xy( measured_x, measured_y, title=None,
                          xlabel=None, ylabel=None,
                          linefmt='r.', linestyle=' ', equal_aspect=True,
                          plotaxis=plotaxis, showplot=True )

    mean_error_vector = np.mean(error_vectors.values(), axis=0)
    logger.info("mean error vector = {}".format( mean_error_vector))
    error_measures = get_measures(error_by_angle.values())
    logger.info("pos ver error_measures= {}".format( error_measures))

    return error_by_angle, expected_points, measured_points, error_measures, mean_error_vector, camera_offset_new, xc, yc
