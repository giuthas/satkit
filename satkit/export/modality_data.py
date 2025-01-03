#
# Copyright (c) 2019-2024
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
Transformers and exporters for Modality data.
"""

from pathlib import Path

import pandas as pd

from satkit.data_structures import Modality, Recording

from .meta_data import export_derived_modalities_meta, export_modality_meta


def modality_data_to_dataframe(
        modality: Modality,
        use_long_time_name: bool = False,
        save_segmentation: bool = False
) -> pd.DataFrame:
    """
    Transforms Modality data to a Pandas dataframe.

    Use with care as a long recording with a complex TextGrid may end up being
    quite large when represented as a DataFrame.

    Parameters
    ----------
    modality : Modality
        Modality whose data is to be transformed.
    use_long_time_name : bool, optional
        Should the column name for used for time include the Modality name, by
        default False.
    save_segmentation : bool, optional
        Should we include columns for each Tier of the corresponding TextGrid,
        by default False. If these are included they will contain the
        corresponding label at each time stamp.

    Returns
    -------
    pd.DataFrame
        The dataframe with columns for at least time stamps and the modality
        data, but also columns for each tier if `save_segmentation` is True.
    """
    data_name = modality.name_underscored
    if use_long_time_name:
        time_name = modality.name_underscored + '_time'
    else:
        time_name = 'time'

    new_df_dict = {
        time_name: modality.modality_data.timevector,
        data_name: modality.modality_data.data,
    }

    if save_segmentation:
        label_dict = modality.owner.satgrid.get_labels(new_df_dict[time_name])
        new_df_dict.update(label_dict)

    return pd.DataFrame(new_df_dict)


def modality_to_csv(
        path: Path | str,
        modality: Modality,
        save_segmentation: bool = False,
        separator: str = '\t'
) -> None:
    """
    Save the Modality to a csv file.

    Parameters
    ----------
    path : Path | str
        Path to the export to.
    modality : Modality
        Modality to export.
    save_segmentation : bool, optional
        Should we include columns for each Tier of the corresponding TextGrid,
        by default False.
    separator : str, optional
        Separator to use in the csv file, by default '\t'.
    """
    if isinstance(path, str):
        path = Path(path)

    if path.suffix != '.csv':
        path = path.with_suffix('.csv')

    dataframe = modality_data_to_dataframe(
        modality=modality, save_segmentation=save_segmentation)
    dataframe.to_csv(
        path, sep=separator, encoding='utf-8', index=False, header=True)
    export_modality_meta(
        filename=path,
        modality=modality,
        description=f"Meta for {modality.name} exported to {path}",)


def derived_modalities_to_csv(
        path: Path | str,
        recording: Recording,
        save_segmentation: bool = False,
) -> None:
    """
    Export all derived Modalities of a Recording to a csv file.

    NOTE: Exporting modalities with different lengths is untested and exporting
    modalities whose data is not 1-D will raise an Error.

    Parameters
    ----------
    path : Path | str
        Path to export to.
    recording : Recording
        Recording whose derived Modalities to export.
    save_segmentation : bool, optional
        Should we include columns for each Tier of the corresponding TextGrid,
        by default False.
    """
    if isinstance(path, str):
        path = Path(path)

    if path.suffix != '.csv':
        path = path.with_suffix('.csv')

    dataframe = pd.concat(
        objs=[
            modality_data_to_dataframe(
                recording[modality_name],
                use_long_time_name=True,
                save_segmentation=save_segmentation,
            )
            for modality_name in recording
            if recording[modality_name].is_derived
        ],
        axis='columns'
    )
    dataframe.to_csv(path, sep='\t', encoding='utf-8', index=False, header=True)
    export_derived_modalities_meta(
        filename=path,
        recording=recording,
        description="Meta for derived Modalities",)
