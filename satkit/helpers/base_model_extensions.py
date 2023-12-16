##
# Copyright (c) 2019-2023
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
##
# This file is part of Speech Articulation ToolKIT
# (see https://github.com/giuthas/satkit/).
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
##
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
##

import logging

from pydantic import BaseModel, Field

_logger = logging.getLogger('satkit.base_model_extensions')

# TODO: write a method that will dump the model in a dict with human readable
# keys. ie. replace underscores with spaces. then make another one that will
# convert in the other direction for the dict to be feedable to inheritors of
# UpdatableBaseModel.


class UpdatableBaseModel(BaseModel):
    """
    An extension of Pydantic BaseModel which can be updated with new data.

    The update will trigger validation again.
    """
    my_field: str = Field(None)

    def update(self, data: dict) -> 'UpdatableBaseModel':
        """
        Update the BaseModel with the contents of data and validate.

        The update does not happen in place but rather a new updated object is
        returned and updating triggers validation.

        Parameters
        ----------
        data : dict
            Only valid key, value pairs are accepted. 

        Returns
        -------
        UpdatableBaseModel
            The updated BaseModel.
        """
        update = self.model_dump()
        update.update(data)
        new_dict = self.model_validate(
            update).model_dump(exclude_defaults=True)
        for key, value in new_dict.items():
            _logger.debug(
                "Updating value of '%s' from '%s' to '%s'.",
                str(key), str(getattr(self, key, None)), str(value))
            setattr(self, key, value)
        return self
