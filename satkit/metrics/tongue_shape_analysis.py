#
# Copyright (c) 2019-2025
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
#
# This file is part of Speech Articulation ToolKIT
# (see https://github.com/giuthas/satkit/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
#
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
#


"""
tshape_analysis - Code for the analysis of tongue shape contours

Original version Copyright (C) 2015 Katherine Dawson <kmdawson8@gmail.com>
Available at https://github.com/kdawson2/tshape_analysis/
"""

import math
import csv
import glob
import os
import logging

import numpy as np

from scipy.integrate import simpson
from scipy.signal import butter, filtfilt

from .spline_metric import SplineShapesEnum

_logger = logging.getLogger('satkit.spline_shape')


def procrustes(reference_shape: np.ndarray,
               compared_shape: np.ndarray) -> float:
    """
    Compare the two shapes with procrustes analysis.

    See Katherine M. Dawson, Mark K. Tiede & D. H. Whalen (2016) Methods for
    quantifying tongue shape and complexity using ultrasound imaging, Clinical
    Linguistics & Phonetics, 30:3-5, 328-344, DOI:
    10.3109/02699206.2015.1099164 for details.


    Parameters
    ----------
    reference_shape : np.ndarray
        the reference spline
    compared_shape : np.ndarray
        the spline to be compared to the reference

    Returns
    -------
    float
        The procrustes similarity value.
    """
    # TODO: this could be done easy enough by just checking if onset has been
    # annotated on a Recording and using that as the reference. however, the
    # same shape maybe should be used for all. problems ensue and an article
    # could be written just on that.

    # translate the points to be centred at 0, 0
    reference_shape = reference_shape.transpose()
    compared_shape = compared_shape.transpose()
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


def modified_curvature_index(data: np.ndarray,
                             run_filter: bool = True) -> float:
    """
    Calculate the modified curvature index.

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
    data : np.ndarray
        one spline with axes ordered: x-y, spline points 
    run_filter : bool
        Should the curvature be filtered before integration.

    Returns
    -------
    float
        the modified curvature index
    """
    # compute signed curvature
    diff_x = np.gradient(data[0, :])
    diff_y = np.gradient(data[1, :])
    diff2_x = np.gradient(diff_x)
    diff2_y = np.gradient(diff_y)
    curvature = (diff_x * diff2_y - diff_y * diff2_x) / (diff_x **
                                                         2 + diff_y**2)**1.5

    cumulative_sum = np.cumsum(
        np.sqrt(np.sum(np.diff(data[0:1, :], axis=1)**2, axis=0)))
    cumulative_sum = np.insert(cumulative_sum, 0, 0)

    if run_filter:
        butter_b, butter_a = butter(5, 1./4.)
        r = curvature[::-1]
        filtered_curvature = filtfilt(
            butter_b, butter_a, np.concatenate((r, curvature, r)))
        filtered_curvature = filtered_curvature[data.shape[1]:-data.shape[1]]

        mci = simpson(np.abs(filtered_curvature), cumulative_sum)
    else:
        mci = simpson(np.abs(curvature), cumulative_sum)

    return mci


def fourier_tongue_shape_analysis(data: np.ndarray) -> np.ndarray:
    """
    Calculate fourier transform of a spline.

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
    tongue_data : np.ndarray
        one spline with axes ordered: x-y, spline points 

    Returns
    -------
    np.ndarray
        array of floats with the axes ordered: 
        real-imaginary-modulus, paramvector
    """
    tangent_angle = np.arctan2(
        np.gradient(data[1, :]),
        np.gradient(data[0, :]))

    ntfm = np.fft.rfft(tangent_angle)

    real = np.real(ntfm)
    imaginary = np.imag(ntfm)
    modulus = np.absolute(ntfm)

    return np.stack([real, imaginary, modulus])


def spline_shape_metric(
        data: np.ndarray,
        metric: SplineShapesEnum,
        notice_base: str) -> np.ndarray:
    """
    Calculate shape spline metrics.

    Parameters
    ----------
    data : np.ndarray
        the spline data
    metric : SplineMetricEnum
        which metric to calculate
    notice_base : str
        text prepended to logging messages

    Returns
    -------
    np.ndarray
        an array of analysis values where array.shape[0] == time_points

    Raises
    ------
    NotImplementedError
        if asked for regular curvature index instead of the modified one.
    NotImplementedError
        if asked for procrustes analysis because passing reference shape in
        hasn't been implemented.
    """

    if metric == SplineShapesEnum.CURVATURE:
        message = "Regular curvature index hasn't been implemented yet."
        message += " Did you mean modified_curvature?"
        raise NotImplementedError(message)

    if metric == SplineShapesEnum.PROCRUSTES:
        message = "Procrustes analysis hasn't been fully implemented yet."
        message += " Passing reference shape in hasn't been implemented."
        raise NotImplementedError(message)

    if metric == SplineShapesEnum.FOURIER:
        if data.shape[2] % 2 == 0:
            result = np.zeros((data.shape[0], 3, int((data.shape[2]/2)+1)))
        else:
            result = np.zeros((data.shape[0], 3, int((data.shape[2]+1)/2)))

        for i in range(data.shape[0]):
            result[i, :, :] = fourier_tongue_shape_analysis(data[i, :])
        _logger.debug("%s: Calculated %s", notice_base, metric)
        return result

    if metric == SplineShapesEnum.MODIFIED_CURVATURE:
        result = np.zeros(data.shape[0])
        for i in range(data.shape[0]):
            result[i] = modified_curvature_index(data[i, :])
        _logger.debug("%s: Calculated %s", notice_base, metric)
        return result


def run_analysis():
    """This is only a place holder function showing how each metric is supposed
    to be run until things are more like SATKIT in general.
    """
    # TODO: move this function and the associated data to tests and ask Kate if
    # it's ok to use her data.

    # name for the data output file
    output_file_name = "shape_analysis_data_out.csv"
    # number of lines to skip for header information in csv files
    n_header_lines = 0

    # make list of csv files in the working directory
    file_list = glob.glob("test_data/*.csv")

    # remove output file from file list
    if output_file_name in file_list:
        file_list.remove(output_file_name)

    # extract ID and symbol info from filename by splitting at last underscore
    file_list = [(f, os.path.splitext(f)[0].rsplit("_", 1)) for f in file_list]

    # find the unique IDs among all files
    ids = set(i[1][0] for i in file_list)

    _logger.debug(
        "Got data for %d unique id(s). %s",
        len(ids), str(ids))

    # open csv file for data output and write header information
    with open(output_file_name, 'w', encoding='utf-8') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            ["ID", "symbol", "repetition", "MCI", "procrustes", "real_1",
             "imag_1", "mod_1", "real_2", "imag_2", "mod_2", "real_3",
             "imag_3", "mod_3"])

        for current_id in ids:
            _logger.debug(
                "Processing data for %s", str(current_id))

            # filter to get the files relevant to the current id
            current_files = [(i[0], i[1][1])
                             for i in file_list if i[1][0] == current_id]

            # filter again to find the resting shape file, which should be
            # ID_rest.csv
            rest_file = [i[0] for i in current_files if i[1] == "rest"]

            # check that there is either 0 or 1 resting shape file
            if len(rest_file) == 0:
                _logger.debug(
                    "No resting shape found for %s.",
                    str(current_id))
                _logger.debug(
                    "Procrustes analysis not available.")
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

                rdata = np.moveaxis(rdata, 0, 1)
                _logger.debug(
                    "Found resting shape")
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
                num_reps = int(data.shape[1]/2)
                _logger.debug(
                    "Found %d shapes for %s", num_reps, symbol)

                # This transforms the test data into the axes
                # time, x-y, spline point
                data = np.stack((data[:, 0::2], data[:, 1::2]))
                data = np.moveaxis(data, (0, 1), (1, 2))

                for rep in range(0, num_reps):
                    # check for NaNs
                    if np.isnan(np.sum(data[rep, :, :])):
                        _logger.debug(
                            "NaN in shape %d ignoring.", rep)
                        continue

                    if do_procrustes:
                        proc = procrustes(rdata, data[rep, :, :])
                    else:
                        proc = 0

                    mci = modified_curvature_index(
                        data[rep, :, :])

                    fourier_params = fourier_tongue_shape_analysis(
                        data[rep, :, :])
                    real = fourier_params[0, :]
                    imaginary = fourier_params[1, :]
                    mod = fourier_params[2, :]

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


if __name__ == '__main__':
    run_analysis()
