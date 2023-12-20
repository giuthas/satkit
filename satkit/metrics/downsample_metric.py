#!/usr/bin/env python3
#
# Copyright (c) 2019-2023
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
Downsampling of metrics and possibly other timeseries data.
"""

from satkit.data_structures import Modality, ModalityData, Recording

# from .pd import PdParameters, PD
# from .spline_metric import SplineMetric


def downsample_modality(
        modality: Modality,
        down_sampling_ratio: int
) -> Modality:
    data = modality.data[::down_sampling_ratio]
    timevector = modality.timevector[::down_sampling_ratio]
    sampling_rate = modality.sampling_rate/down_sampling_ratio

    modality_data = ModalityData(
        data=data, timevector=timevector, sampling_rate=sampling_rate)

    return modality.__class__(
        modality.recording,
        parsed_data=modality_data,
        metadata=modality.metadata.model_copy(),
        meta_path=modality.meta_path,
        load_path=modality.load_path,
        time_offset=modality.time_offset)


def downsample_metrics(
        recording: Recording,
        modality_pattern: str,
        down_sampling_ratios: tuple[int],
        match_timestep: bool = True
) -> None:

    modalities = [recording.modalities[key]
                  for key in recording.modalities
                  if modality_pattern in key]

    if match_timestep:
        modalities = [
            modality for modality in modalities
            if modality.metadata.timestep in down_sampling_ratios]

        for modality in modalities:
            downsampled = downsample_modality(
                modality, modality.metadata.timestep)
            recording.add_modality(downsampled)

    else:
        raise NotImplementedError(
            "Downsampling without matching the downsampling "
            "step to the timestep of the modality has not been "
            "implemented yet.")
