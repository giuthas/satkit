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

from .meta_data import export_modality_meta


def modality_data_to_dataframe(modality: Modality) -> pd.DataFrame:
    data_name = modality.name_underscored

    new_df_dict = {
        'time': modality.modality_data.timevector,
        data_name: modality.modality_data.data,
    }

    return pd.DataFrame(new_df_dict)


def modality_to_csv(path: Path | str, modality: Modality) -> None:
    if isinstance(path, str):
        path = Path(path)

    if path.suffix != '.csv':
        path = path.with_suffix('.csv')

    dataframe = modality_data_to_dataframe(modality)
    dataframe.to_csv(path, sep='\t', encoding='utf-8', index=False, header=True)
    export_modality_meta(
        filename=path,
        modality=modality,
        description=f"Meta for {modality.name} exported to {path}",)


def modalities_to_csv(path: Path | str, recording: Recording) -> None:
    if isinstance(path, str):
        path = Path(path)

    if path.suffix != '.csv':
        path = path.with_suffix('.csv')

