

"""
tshape_analysis - Code for the analysis of tongue shape contours

Original version Copyright (C) 2015 Katherine Dawson <kmdawson8@gmail.com>
Available at https://github.com/kdawson2/tshape_analysis/
"""

import math
import csv
import glob
import os

import numpy as np

from scipy.integrate import simpson
from scipy.signal import butter, filtfilt


def procrustes(reference_shape: np.ndarray, compared_shape: np.ndarray):
    """
    _summary_

    See Katherine M. Dawson, Mark K. Tiede & D. H. Whalen (2016) Methods for
    quantifying tongue shape and complexity using ultrasound imaging, Clinical
    Linguistics & Phonetics, 30:3-5, 328-344, DOI:
    10.3109/02699206.2015.1099164 for details.


    Parameters
    ----------
    reference_shape : np.ndarray
        _description_
    compared_shape : np.ndarray
        _description_

    Returns
    -------
    _type_
        _description_
    """

    # translate the points to be centred at 0, 0
    normalised_reference = reference_shape - reference_shape.mean(axis=0)
    normalised_compared = compared_shape - compared_shape.mean(axis=0)

    # scale the points to have unit variance.
    normalised_reference /= np.sqrt((normalised_reference **
                                    2.0).sum(axis=1).mean())
    normalised_compared /= np.sqrt((normalised_compared **
                                   2.0).sum(axis=1).mean())

    # find the optimum rotation angle
    num = (
        normalised_compared[:, 0] * normalised_reference[:, 1] -
        normalised_compared[:, 1] * normalised_reference[:, 0]).sum()
    denom = (
        normalised_compared[:, 0] * normalised_reference[:, 0] +
        normalised_compared[:, 1] * normalised_reference[:, 1]).sum()
    theta = math.atan2(num, denom)

    # rotate the b points onto a
    r_matrix = np.array([[math.cos(theta), -math.sin(theta)],
                        [math.sin(theta), math.cos(theta)]])
    b2 = np.dot(r_matrix, normalised_compared.transpose()).transpose()

    # compute the error metric
    return math.sqrt(((normalised_reference - b2)**2.0).sum())


def modified_curvature_index(data):
    """
    Calculate the modified curvature index.

    NOTE: remains to be seen what we are going to calculate this on in SATKIT.

    The results are smoothed with a 5th order Butterworth lowpass filter with a
    critical frequency of 1/4. The filter is applied both forwards and
    backwards to padded data with filtfilt. Padding is removed before returning
    the results.

    See Katherine M. Dawson, Mark K. Tiede & D. H. Whalen (2016) Methods for
    quantifying tongue shape and complexity using ultrasound imaging, Clinical
    Linguistics & Phonetics, 30:3-5, 328-344, DOI:
    10.3109/02699206.2015.1099164 for details.

    Parameters
    ----------
    data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """

    # compute signed curvature
    diff_x = np.gradient(data[:, 0])
    diff_y = np.gradient(data[:, 1])
    diff2_x = np.gradient(diff_x)
    diff2_y = np.gradient(diff_y)
    curvature = (diff_x * diff2_y - diff_y * diff2_x) / (diff_x **
                                                         2 + diff_y**2)**1.5

    cumulative_sum = np.cumsum(
        np.sqrt(np.sum(np.diff(data, axis=0)**2, axis=1)))
    cumulative_sum = np.insert(cumulative_sum, 0, 0)

    butter_b, butter_a = butter(5, 1./4.)
    r = curvature[::-1]
    filtered_curvature = filtfilt(
        butter_b, butter_a, np.concatenate((r, curvature, r)))
    filtered_curvature = filtered_curvature[len(data):-len(data)]

    mci = simpson(np.abs(filtered_curvature), cumulative_sum)

    return mci


def fourier_tongue_shape_analysis(tongue_data: np.ndarray):
    """
    _summary_

    The output of the DFT analysis for our purposes is the value of a given
    shape provided by the ﬁrst three Fourier coeﬃcients. The ﬁrst coeﬃcient of
    the Fourier transform (C1) corresponds to the largest scale features of the
    shape. The higher coeﬃcients reﬂect smaller scale features. Very high
    coeﬃcients represent small variations in the shape, often introduced during
    the contour ﬁtting procedure (i.e. noise). Hence, coeﬃcients above the
    third (C3) are not included in this analysis. Each coeﬃcient has a real and
    an imaginary part, and the location of a data point on these real and
    imaginary axes can be described in radial coordinates, giving the
    corresponding phase and magnitude of the coeﬃcient.

    See Katherine M. Dawson, Mark K. Tiede & D. H. Whalen (2016) Methods for
    quantifying tongue shape and complexity using ultrasound imaging, Clinical
    Linguistics & Phonetics, 30:3-5, 328-344, DOI:
    10.3109/02699206.2015.1099164 for details.

    Parameters
    ----------
    data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """

    # TODO: possibly misnamed variable, check the article for what this is
    # actually supposed to be.
    radians = np.arctan2(
        np.gradient(tongue_data[:, 1]),
        np.gradient(tongue_data[:, 0]))

    ntfm = np.fft.rfft(radians)

    real = np.real(ntfm)
    imaginary = np.imag(ntfm)
    mod = np.absolute(ntfm)

    return real, imaginary, mod


def run_analysis():
    """This is only a place holder function showing how each metric is supposed
    to be run until things are more like SATKIT in general."""
    # name for the data output file
    output_file_name = "shape_analysis_data_out.csv"
    # number of lines to skip for header information in csv files
    n_header_lines = 0

    # make list of csv files in the working directory
    file_list = glob.glob("*.csv")

    # remove output file from file list
    if output_file_name in file_list:
        file_list.remove(output_file_name)

    # extract ID and symbol info from filename by splitting at last underscore
    file_list = [(f, os.path.splitext(f)[0].rsplit("_", 1)) for f in file_list]

    # find the unique IDs among all files
    ids = set(i[1][0] for i in file_list)

    print(f"Got data for {len(ids)} unique id(s). {ids}")

    # open csv file for data output and write header information
    with open(output_file_name, 'wb') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            ["ID", "symbol", "repetition", "MCI", "procrustes", "real_1",
             "imag_1", "mod_1", "real_2", "imag_2", "mod_2", "real_3",
             "imag_3", "mod_3"])

        for current_id in ids:

            print("Processing data for {current_id}")

            # filter to get the files relevant to the current id
            current_files = [(i[0], i[1][1])
                             for i in file_list if i[1][0] == current_id]

            # filter again to find the resting shape file, which should be
            # ID_rest.csv
            rest_file = [i[0] for i in current_files if i[1] == "rest"]

            # check that there is either 0 or 1 resting shape file
            if len(rest_file) == 0:
                print(
                    f"No resting shape found for {current_id}"
                    f" Procrustes analysis not available")
                do_procrustes = False
            elif len(rest_file) == 1:
                do_procrustes = True
                rdata = np.genfromtxt(
                    rest_file[0],
                    delimiter=",", skip_header=n_header_lines)
                # there should only be one shape in the resting shape file
                if rdata.shape[1] != 2:
                    raise IOError(
                        "There should be one and only one "
                        "shape in the resting shape file")
                print("Found resting shape")
            else:
                assert False, "This can't happen"

            # loop over all the files for the current id
            for file_name, symbol in current_files:

                # skip the resting shape file
                if symbol == "rest":
                    continue

                data = np.genfromtxt(
                    file_name, delimiter=",", skip_header=n_header_lines)

                if data.shape[1] % 2 != 0:
                    raise IOError(
                        "Number of data columns not a multiple of 2 in " +
                        str(file_name))
                num_reps = data.shape[1]/2
                print(f"Found {num_reps} shapes for {symbol}")

                for rep in range(0, num_reps):

                    j = 2*rep

                    # check for NaNs
                    if np.isnan(np.sum(data[:, j:j+2])):
                        print(f"NaN in shape {rep} ignoring.")
                        continue

                    if do_procrustes:
                        proc = procrustes(rdata, data[:, j:j+2])
                    else:
                        proc = 0

                    mci = modified_curvature_index(data[:, j:j+2])

                    real, imaginary, mod = fourier_tongue_shape_analysis(
                        data[:, j: j + 2])

                    writer.writerow(
                        [current_id, symbol, rep, mci, proc, real[1],
                         imaginary[1],
                         mod[1],
                         real[2],
                         imaginary[2],
                         mod[2],
                         real[3],
                         imaginary[3],
                         mod[3]])
