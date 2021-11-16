#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, Matthew Faytak,
# and Motoki Saito.
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

import numpy as np
import cv2
from scipy import ndimage
import math
from tqdm import tqdm


def to_fan(imgs, angle=None, zero_offset=None, pix_per_mm=None,
           num_vectors=None, magnify=1, reserve=1800, show_progress=False):
    if len(imgs.shape) == 4:  # multiple RGB images
        if show_progress:
            imgs = [
                to_fan_2d(
                    i, angle, zero_offset, pix_per_mm, num_vectors,
                    magnify, reserve)
                for i in tqdm(imgs, desc='Fanshape')]
        else:
            imgs = [
                to_fan_2d(
                    i, angle, zero_offset, pix_per_mm, num_vectors,
                    magnify, reserve) for i in imgs]
    elif len(imgs.shape) == 3:
        if imgs.shape[-1] == 3:  # single RGB image
            imgs = to_fan_2d(imgs, angle, zero_offset,
                             pix_per_mm, num_vectors, magnify, reserve)
        else:  # multiple grayscale images
            if show_progress:
                imgs = [
                    to_fan_2d(
                        i, angle, zero_offset, pix_per_mm, num_vectors,
                        magnify, reserve)
                    for i in tqdm(imgs, desc='Fanshape')]
            else:
                imgs = [
                    to_fan_2d(
                        i, angle, zero_offset, pix_per_mm, num_vectors,
                        magnify, reserve) for i in imgs]
    else:  # single grayscale image
        imgs = to_fan_2d(imgs, angle, zero_offset, pix_per_mm,
                         num_vectors, magnify, reserve)
    return np.array(imgs)


def to_fan_2d(img, angle=None, zero_offset=None, pix_per_mm=None,
              num_vectors=None, magnify=1, reserve=1800):

    use_genpar = any([i is None
                      for i in [angle, zero_offset, pix_per_mm, num_vectors]])
    if use_genpar:
        print('WARNING: Not all the necessary information are provided. General parameters are used instead.')
        img = cv2.resize(img, (500, 500))
        angle = 0.0031
        zero_offset = 150
        pix_per_mm = 2
        num_vectors = img.shape[0]

    pix_per_mm = pix_per_mm//magnify

    img = np.rot90(img, 3)
    dimnum = len(img.shape)
    if dimnum == 2:
        grayscale = True
    elif dimnum == 3 and img.shape[-1] == 3:
        grayscale = False
    else:
        raise ValueError(
            'Dimensions are not 2. And it does not look like a RGB format, either.')

    if grayscale:
        output_shape = (
            int(reserve // pix_per_mm),
            int((reserve * 0.80) // pix_per_mm))
    else:
        output_shape = (
            int(reserve // pix_per_mm),
            int((reserve * 0.80) // pix_per_mm),
            3)
    origin = (int(output_shape[0] // 2), 0)

    img = ndimage.geometric_transform(img,
                                      mapping=ult_cart2pol,
                                      output_shape=output_shape,
                                      order=2,
                                      cval=255,
                                      extra_keywords={
                                          'origin': origin,
                                          'num_of_vectors': num_vectors,
                                          'angle': angle,
                                          'zero_offset': zero_offset,
                                          'pix_per_mm': pix_per_mm,
                                          'grayscale': grayscale})
    img = trim_picture(img)
    img = np.rot90(img, 1)
    return img


def ult_cart2pol(
        output_coordinates, origin, num_of_vectors, angle, zero_offset,
        pix_per_mm, grayscale):
    def cart2pol(x, y):
        r = math.sqrt(x**2 + y**2)
        th = math.atan2(y, x)
        return r, th
    (r, th) = cart2pol(output_coordinates[0] - origin[0],
                       output_coordinates[1] - origin[1])
    r *= pix_per_mm
    cl = num_of_vectors // 2
    if grayscale:
        res = cl - ((th - np.pi / 2) / angle), r - zero_offset
    else:
        res = cl - ((th - np.pi / 2) / angle), r - \
            zero_offset, output_coordinates[2]
    return res


def trim_picture(img):
    def unique_element_number(vec):
        try:
            aaa = [tuple(i) for i in vec]
        except TypeError:
            aaa = vec
        try:
            res = len(set(aaa))
        except TypeError:
            print('Warning: the input is not iterable')
            res = 1
        return res

    if len(img.shape) == 2:
        unique_column = np.apply_along_axis(unique_element_number, 0, img)
        img = img[:, unique_column != 1]
        unique_row = np.apply_along_axis(unique_element_number, 1, img)
        img = img[unique_row != 1, :]
    elif len(img.shape) == 3:
        unique_row = np.array([unique_element_number(i) for i in img])
        img = img[unique_row != 1, :, :]
        unique_column = np.array([unique_element_number(
            img[:, i, :]) for i in range(img.shape[1])])
        img = img[:, unique_column != 1, :]
    return img
