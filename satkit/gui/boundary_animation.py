#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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

from dataclasses import dataclass
from typing import Optional

from matplotlib.lines import Line2D as mpl_line_2d
from matplotlib.text import Text as mpl_text
from satkit.data_structures.satgrid import SatInterval


@dataclass
class AnimatableBoundary:
    """
    GUI/matplotlib elements of a rendered boundary.
    
    These are: one line and the previous and following label.
    """
    line: mpl_line_2d
    prev_text: Optional[mpl_text] = None
    next_text: Optional[mpl_text] = None

class BoundaryAnimator:
    """
    Draggable annotation boundary with blitting.

    The class allows only one boundary to be moved at a time. If another
    boundary is crossed then this boundary will return to its original position
    on mouse release. Otherwise, the boundary will stay where it is at mouse
    release and  the underlying Interval gets updated with the new position.
    """

    lock = None  # only one boundary can be animated at a time

    def __init__(self, 
            boundary: AnimatableBoundary, 
#            data_axes, 
            segment :Optional[SatInterval]=None, 
            time_offset=0):
        self.boundary = boundary
#        self.data_axes = data_axes
        self.segment = segment
        self.time_offset = time_offset
        self.press = None
        self.backgrounds = []

    def connect(self):
        """Connect to all the events we need."""
        self.cidpress = self.boundary.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.boundary.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.boundary.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        if BoundaryAnimator.lock is not None:
            return

        is_inaxes = False
        for line in self.boundary.lines:
            if (event.inaxes == line.axes):
                is_inaxes = True
        if not is_inaxes:
            return

        some_line_contains = False
        for line in self.boundary.lines:
            contains, attrd = line.contains(event)
            if contains:
                some_line_contains = True
                break
        if not some_line_contains:
            return

        self.press = line.get_data(), (event.xdata, event.ydata)
        BoundaryAnimator.lock = self

        # draw everything but the selected line and store the pixel buffer
        line = self.boundary.line
        prev_text = self.boundary.prev_text
        next_text = self.boundary.next_text
        canvas = line.figure.canvas
        axes = line.axes

        line.set_animated(True)
        if prev_text:
            prev_text.set_animated(True)
        if next_text:
            next_text.set_animated(True)

        canvas.draw()
        self.backgrounds.append(canvas.copy_from_bbox(line.axes.bbox))

        # now redraw just the line
        axes.draw_artist(line)
        if prev_text:
            axes.draw_artist(prev_text)
        if next_text:
            axes.draw_artist(next_text)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        """Move the boundary if the mouse is over us."""
        if BoundaryAnimator.lock is not self:
            return

        is_inaxes = False
        for line in self.annotation:
            if (event.inaxes == line.axes):
                is_inaxes = True
        if not is_inaxes:
            return

        (x0, y0), (xpress, ypress) = self.press
        dx = event.xdata - xpress
        if self.segment.is_legal_value(x0[0]+dx+self.time_offset):
            for i, line in enumerate(self.annotation):
                line.set(xdata=x0+dx)
                self.segment.begin = x0[0] + dx + self.time_offset

                canvas = line.figure.canvas
                axes = line.axes
                # restore the background region
                canvas.restore_region(self.backgrounds[i])

                # redraw just the current rectangle
                axes.draw_artist(line)

                # blit just the redrawn area
                canvas.blit(axes.bbox)

    def on_release(self, event):
        """Clear button press information."""
        if BoundaryAnimator.lock is not self:
            return

        self.press = None
        BoundaryAnimator.lock = None

        # turn off the rect animation property and reset the background
        for line in self.annotation:
            line.set_animated(False)
            # redraw the full figure
            line.figure.canvas.draw()

        self.backgrounds = []

    def disconnect(self):
        """Disconnect all callbacks."""
        for line in self.annotation:
            line.figure.canvas.mpl_disconnect(self.cidpress)
            line.figure.canvas.mpl_disconnect(self.cidrelease)
            line.figure.canvas.mpl_disconnect(self.cidmotion)
