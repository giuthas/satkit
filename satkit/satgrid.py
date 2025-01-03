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
SatGrid and its components are a GUI friendly encapsulation of
`textgrids.TextGrid`.
"""
from abc import ABC, abstractmethod
from collections import OrderedDict

import numpy as np
from textgrids import Interval, Point, TextGrid, Tier, Transcript
from textgrids.templates import (long_header, long_interval, long_point,
                                 long_tier)
from typing_extensions import Self

from satkit.constants import IntervalCategory


class SatAnnotation(ABC):
    """Base class for Textgrid Point and Interval to enable editing with GUI."""

    def __init__(
            self,
            time: float,
            label: None | Transcript,
    ) -> None:
        self._time = time
        self.label = label

    @abstractmethod
    def contains(self, time: float) -> bool:
        """
        Does this Interval contain `time` or is this Point at `time`.

        'Being at time' is defined in the sense of 'within epsilon of time'.

        Parameters
        ----------
        time : float
            The time in seconds to test against this Annotation.

        Returns
        -------
            bool
            True if `time` is in this Interval or at this Point.
        """


class SatPoint(SatAnnotation):
    """TextGrid Point representation to enable editing with GUI."""

    @classmethod
    def from_textgrid_point(
            cls,
            point: Point,
    ) -> Self:
        """
        Copy the info of a Python TextGrids Interval into a new SatInterval.

        Only xmin and text are copied from the original Interval. xmax is
        assumed to be handled by either the next SatInterval or the
        constructing method if this is the last Interval.

        Since SatIntervals are doubly linked, an attempt will be made to link
        prev and next to this interval.

        Returns the newly created SatInterval.
        """
        return cls(
            time=point.xpos,
            label=point.text,
        )

    def __init__(
            self,
            time: float,
            label: None | Transcript
    ) -> None:
        super().__init__(time=time, label=label)

    @property
    def time(self) -> float:
        """Location of this Point."""
        return self._time

    @time.setter
    def time(self, time: float) -> None:
        self._time = time

    def contains(self, time: float) -> bool:
        epsilon = config_dict['epsilon']
        if self._time - epsilon < time < self._time + epsilon:
            return True
        return False


class SatInterval(SatAnnotation):
    """TextGrid Interval representation to enable editing with GUI."""

    @classmethod
    def from_textgrid_interval(
        cls,
        interval: Interval,
        prev_interval: None | Self,
        next_interval: None | Self = None
    ) -> Self:
        """
        Copy the info of a Python TextGrids Interval into a new SatInterval.

        Only xmin and text are copied from the original Interval. xmax is
        assumed to be handled by either the next SatInterval or the
        constructing method if this is the last Interval. 

        Since SatIntervals are doubly linked, an attempt will be made to link
        prev and next to this interval. 

        Returns the newly created SatInterval.
        """
        return cls(
            begin=interval.xmin,
            label=interval.text,
            prev_interval=prev_interval,
            next_interval=next_interval)

    def __init__(self,
                 begin: float,
                 label: None | Transcript,
                 prev_interval: None | Self = None,
                 next_interval: None | Self = None) -> None:
        super().__init__(
            time=begin,
            label=label,
        )

        self._prev_interval = prev_interval
        if self.prev:
            self.prev._next_interval = self

        self._next_interval = next_interval
        if self.next:
            self.next.prev = self

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}: text: '{self.label}'\t "
                f"begin: {self.begin}, end: {self.end}")

    @property
    def next(self) -> Self | None:
        """The next annotation, if any."""
        return self._next_interval

    @next.setter
    def next(self, next_interval: Self | None) -> None:
        if next_interval != self._next_interval:
            self._next_interval = next_interval

    @property
    def prev(self) -> Self | None:
        """The previous annotation, if any."""
        return self._prev_interval

    @prev.setter
    def prev(self, prev_interval: Self | None) -> None:
        if prev_interval != self._prev_interval:
            self._prev_interval = prev_interval

    @property
    def begin(self) -> float:
        """Beginning time point of the interval."""
        return self._time

    @begin.setter
    def begin(self, value: float) -> None:
        self._time = value

    @property
    def mid(self) -> float | None:
        """
        Middle time point of the interval.

        This is a property that will return None
        if this Interval is the one that marks
        the last boundary.
        """
        if self._next_interval:
            return (self.begin + self._next_interval.begin)/2
        return None

    @property
    def end(self) -> float | None:
        """
        End time point of the interval.

        This is a property that will return None
        if this Interval is the one that marks
        the last boundary.
        """
        if self._next_interval:
            return self._next_interval.begin
        return None

    @end.setter
    def end(self, value: float) -> None:
        if self._next_interval:
            self._next_interval.begin = value

    def is_at_time(self, time: float, epsilon) -> bool:
        """
        Intervals are considered equivalent if the difference between their
        `begin` values is < epsilon. Epsilon is a constant defined in SATKIT's
        configuration.
        """
        return abs(self.begin - time) < epsilon

    def is_last(self) -> bool:
        """Is this the last Interval in this Tier."""
        return self._next_interval is None

    def is_legal_value(self, time: float, epsilon: float) -> bool:
        """
        Check if the given time is between the previous and next boundary.

        Usual caveats about float testing don't apply, because each boundary is
        padded with SATKIT epsilon. Tests used do not include equality with
        either bounding boundary, and that may or may not be trusted to be the
        actual case depending on how small the epsilon is.

        Returns True, if time is  between the previous and next boundary.
        """
        return (time + epsilon < self._next_interval.begin and
                time > epsilon + self.prev.begin)

    def contains(self, time: float) -> bool:
        if self.begin < time < self.end:
            return True
        return False


class SatTier(list):
    """TextGrid Tier representation to enable editing with GUI."""

    @classmethod
    def from_textgrid_tier(cls, tier: Tier) -> Self:
        """
        Copy a Python TextGrids Tier as a SatTier.

        Returns the newly created SatTier.
        """
        return cls(tier)

    def __init__(self, tier: Tier) -> None:
        super().__init__()
        last_interval = None
        prev = None
        for interval in tier:
            current = SatInterval.from_textgrid_interval(interval, prev)
            self.append(current)
            prev = current
            last_interval = interval
        self.append(SatInterval(last_interval.xmax, None, prev))

    def __repr__(self) -> str:
        representation = f"{self.__class__.__name__}:\n"
        for interval in self:
            representation += str(interval) + "\n"
        return representation

    @property
    def begin(self) -> float:
        """
        Begin timestamp.

        Corresponds to a TextGrid Interval's xmin.

        This is a property and the actual value is generated from the first
        SatInterval of this SatTier.
        """
        return self[0].begin

    @property
    def end(self) -> float:
        """
        End timestamp.

        Corresponds to a TextGrid Interval's xmin.

        This is a property and the actual value is generated from the last
        SatInterval of this SatTier.
        """
        # This is slightly counterintuitive, but the last interval is in fact
        # empty and only represents the final boundary. So its `begin` is the
        # final boundary.
        return self[-1].begin

    @property
    def is_point_tier(self) -> bool:
        """Is this Tier a PointTier."""
        return False

    def boundary_at_time(
            self, time: float, epsilon: float) -> SatInterval | None:
        """
        If there is a boundary at time, return it.

        Returns None, if there is no boundary at time. 

        'Being at time' is defined as being within SATKIT epsilon of the given
        timestamp.
        """
        for interval in self:
            if interval.is_at_time(time=time, epsilon=epsilon):
                return interval
        return None

    def get_interval_by_category(
        self,
        interval_category: IntervalCategory,
        label: str | None = None
    ) -> SatInterval:
        """
        Return the Interval matching the category in this Tier.

        If interval_category is FIRST_LABELED or LAST_LABELED, the label should
        be specified as well.

        Parameters
        ----------
        interval_category : IntervalCategory
            The category to search for.
        label : Optional[str], optional
            Label to search for when doing a label based category search, by
            default None

        Returns
        -------
        SatInterval
            _description_
        """
        if interval_category is IntervalCategory.FIRST_NON_EMPTY:
            for interval in self:
                if interval.label:
                    return interval

        if interval_category is IntervalCategory.LAST_NON_EMPTY:
            for interval in reversed(self):
                if interval.label:
                    return interval

        if interval_category is IntervalCategory.FIRST_LABELED:
            for interval in self:
                if interval.label == label:
                    return interval

        if interval_category is IntervalCategory.LAST_LABELED:
            for interval in reversed(self):
                if interval.label == label:
                    return interval

    def get_labels(self, time_vector: np.ndarray) -> np.ndarray:
        """
        Get the labels at the times in the `time_vector`.

        Parameters
        ----------
        time_vector : np.ndarray
            Time stamps to retrieve the labels for.

        Returns
        -------
            np.ndarray
            This array contains the labels as little endian Unicode strings.
        """
        max_label = max(
            [len(element.label) for element in self
             if element.label is not None]
        )
        labels = np.empty(len(time_vector), dtype=f"<U{max_label}")
        for (i, time) in enumerate(time_vector):
            labels[i] = self.label_at(time)
        return labels

    def label_at(self, time: float) -> str:
        """
        Get the label at the given time.

        Parameters
        ----------
        time : float
            Time in seconds to retrieve the label for.

        Returns
        -------
            The label string.
        """
        if time < self.begin or time > self.end:
            return ""

        for element in self:
            if element.contains(time):
                return element.label


class SatGrid(OrderedDict):
    """
    TextGrid representation which makes editing easier.

    SatGrid is a OrderedDict very similar to Python textgrids TextGrid, but
    made up of SatTiers that in turn contain intervals or points as doubly
    linked lists instead of just lists. See the relevant classes for more
    details.
    """

    def __init__(self, textgrid: TextGrid) -> None:
        super().__init__()
        for tier_name in textgrid:
            self[tier_name] = SatTier.from_textgrid_tier(textgrid[tier_name])

    # def as_textgrid(self):
    #     pass

    @property
    def begin(self) -> float:
        """
        Begin timestamp.

        Corresponds to a TextGrids xmin.

        This is a property and the actual value is generated from the first
        SatTier of this SatGrid.
        """
        key = list(self.keys())[0]
        return self[key].begin

    @property
    def end(self) -> float:
        """
        End timestamp.

        Corresponds to a TextGrids xmax.

        This is a property and the actual value is generated from the first
        SatTier of this SatGrid.
        """
        # First Tier
        key = list(self.keys())[0]
        # Return the end of the first Tier.
        return self[key].end

    def format_long(self) -> str:
        """Format self as long format TextGrid."""
        out = long_header.format(self.begin, self.end, len(self))
        tier_count = 1
        for name, tier in self.items():
            if tier.is_point_tier:
                tier_type = 'PointTier'
                elem_type = 'points'
            else:
                tier_type = 'IntervalTier'
                elem_type = 'intervals'
            out += long_tier.format(tier_count,
                                    tier_type,
                                    name,
                                    self.begin,
                                    self.end,
                                    elem_type,
                                    len(tier)-1)
            for elem_count, elem in enumerate(tier, 1):
                if tier.is_point_tier:
                    out += long_point.format(elem_count,
                                             elem.time,
                                             elem.label)
                elif elem.next:
                    out += long_interval.format(elem_count,
                                                elem.begin,
                                                elem.end,
                                                elem.label)
                else:
                    # The last interval does not contain anything.
                    # It only marks the end of the file and final
                    # interval's end. That info got already used by
                    # elem.end (which is elem.next.begin) above.
                    pass
        return out

    def get_labels(self, time_vector: np.ndarray) -> dict[str, np.ndarray]:
        """
        Get the

        Parameters
        ----------
        time_vector :

        Returns
        -------

        """
        labels = {}
        for tier_name in self:
            labels[tier_name] = self[tier_name].get_labels(time_vector)

        return labels
