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
"""Classes for animating TextGrid boundaries."""

from dataclasses import dataclass
from typing import List, Optional

from matplotlib.axes import Axes
from matplotlib.lines import Line2D as mpl_line_2d
from matplotlib.text import Text as mpl_text
from satkit.satgrid import SatInterval


@dataclass
class AnimatableBoundary:
    """
    GUI/matplotlib elements of a rendered boundary.

    These are: one line and the previous and following label.
    """
    axes: Axes
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

    def __init__(
            self,
            main_window,
            boundaries: List[AnimatableBoundary],
            segment: SatInterval,
            epsilon: float,
            time_offset=0
    ):
        self.main_window = main_window
        self.boundaries = boundaries
        self.segment = segment
        self.epsilon = epsilon
        self.time_offset = time_offset

        self.press = None
        self.backgrounds = []
        self.shift_is_held = False
        # We generate this dynamically every time a shift-drag occurs.
        self.coincident_boundaries = []

        self.cidpress = None
        self.cidmotion = None
        self.cidrelease = None

    def connect(self):
        """Connect to all the events we need."""
        for boundary in self.boundaries:
            self.cidpress = boundary.line.figure.canvas.mpl_connect(
                'button_press_event', self.on_press)
            self.cidrelease = boundary.line.figure.canvas.mpl_connect(
                'button_release_event', self.on_release)
            self.cidmotion = boundary.line.figure.canvas.mpl_connect(
                'motion_notify_event', self.on_motion)

    def disconnect(self):
        """Disconnect all callbacks."""
        for boundary in self.boundaries:
            boundary.line.figure.canvas.mpl_disconnect(self.cidpress)
            boundary.line.figure.canvas.mpl_disconnect(self.cidrelease)
            boundary.line.figure.canvas.mpl_disconnect(self.cidmotion)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        if BoundaryAnimator.lock is not None:
            return

        # Store the state of shift at the beginning of the press.
        # This will be released locally in this class at the end.
        if self.main_window.shift_is_held:
            self.shift_is_held = True
            for animator in self.main_window.animators:
                if (animator is not self and
                        animator.segment.begin == self.segment.begin):
                    self.coincident_boundaries.append(animator)
                    print(
                        f"self: {self.segment.label} {self.segment.begin} "
                        f"other:{animator.segment.label}"
                        f" {animator.segment.begin}")

        is_inaxes = False
        for boundary in self.boundaries:
            if event.inaxes == boundary.axes:
                is_inaxes = True
        if not is_inaxes:
            return

        some_line_contains = False
        for boundary in self.boundaries:
            if boundary.line.contains(event)[0]:
                some_line_contains = True
                self.press = boundary.line.get_data()[0], event.xdata
                break
        if not some_line_contains:
            return

        BoundaryAnimator.lock = self

        # draw everything but the selected line and store the pixel buffer
        # TODO: don't draw coinciding lines if shift was held
        axes = None
        canvas = None
        for boundary in self.boundaries:
            line = boundary.line
            prev_text = boundary.prev_text
            next_text = boundary.next_text
            canvas = line.figure.canvas
            axes = boundary.axes

            line.set_animated(True)
            if prev_text:
                prev_text.set_animated(True)
            if next_text:
                next_text.set_animated(True)

            canvas.draw()
            self.backgrounds.append(canvas.copy_from_bbox(line.axes.bbox))

            # now redraw just the animated elements
            axes.draw_artist(line)
            if prev_text:
                axes.draw_artist(prev_text)
            if next_text:
                axes.draw_artist(next_text)

        # and blit just the redrawn area
        if canvas and axes:
            canvas.blit(axes.bbox)

    def on_motion(self, event):
        """Move the boundary if the mouse is over us."""
        if BoundaryAnimator.lock is not self:
            return

        is_inaxes = False
        for boundary in self.boundaries:
            if event.inaxes == boundary.axes:
                is_inaxes = True
        if not is_inaxes:
            return

        x0, xpress = self.press
        dx = event.xdata - xpress
        # Prevent boundary crossings.
        if self.segment.is_legal_value(
                time=x0[0] + dx + self.time_offset, epsilon=self.epsilon
        ):
            for i, boundary in enumerate(self.boundaries):
                self.segment.begin = x0[0] + dx + self.time_offset

                boundary.line.set(xdata=x0 + dx)

                if boundary.prev_text:
                    boundary.prev_text.set(
                        x=self.segment.prev.mid - self.time_offset)
                if boundary.next_text:
                    boundary.next_text.set(
                        x=self.segment.mid - self.time_offset)

                canvas = boundary.line.figure.canvas
                axes = boundary.axes
                # restore the background region
                canvas.restore_region(self.backgrounds[i])

                # redraw just the current rectangle
                axes.draw_artist(boundary.line)
                if boundary.prev_text:
                    axes.draw_artist(boundary.prev_text)
                if boundary.next_text:
                    axes.draw_artist(boundary.next_text)

                # blit just the redrawn area
                canvas.blit(axes.bbox)

    def on_release(self, event):
        """Clear button press information."""
        if BoundaryAnimator.lock is not self:
            self.main_window.onpick(event)
            return

        self.press = None
        BoundaryAnimator.lock = None
        # We generate this dynamically every time a shift-drag occurs.
        self.coincident_boundaries = []
        self.shift_is_held = False

        # turn off the rect animation property and reset the background
        for boundary in self.boundaries:
            boundary.line.set_animated(False)
            if boundary.prev_text:
                boundary.prev_text.set_animated(False)
            if boundary.next_text:
                boundary.next_text.set_animated(False)

            # redraw the full figure
            if hasattr(boundary.line.figure, 'canvas'):
                boundary.line.figure.canvas.draw()

        self.backgrounds = []
