
from collections import OrderedDict
from dataclasses import dataclass
from typing import Union

from textgrids import Interval, TextGrid, Tier, Transcript
from textgrids.templates import (long_header, long_interval, long_point,
                                 long_tier)
from typing_extensions import Self


class SatInterval:
    """TextGrid Interval represantation to enable editing with GUI."""

    def __init__(self, 
            begin: float, 
            text: Union[None, Transcript], 
            prev: Union[None, Self]=None,
            next: Union[None, Self]=None) -> None:
        self.begin = begin
        self.text = text

        self.prev = prev
        if self.prev:
            self.prev.next = self

        self.next = next
        if self.next:
            self.next.prev = self

    @property
    def mid(self) -> Union[float, None]:
        if self.text:
            return (self.begin+self.next.begin)/2
        else:
            return None

    @classmethod
    def from_textgrid_interval(cls, 
        interval: Interval, 
        prev: Union[None, Self], 
        next: Union[None, Self]=None) -> Self:
        return cls(
            begin=interval.xmin,
            text=interval.text,
            prev=prev,
            next=next)

class SatTier(list):
    """TextGrid Tier represantation to enable editing with GUI."""

    def __init__(self, tier: Tier) -> None:
        last_interval = None
        prev = current = None
        for interval in tier:
            current = SatInterval.from_textgrid_interval(interval, prev)
            self.append(current)
            prev = current 
            last_interval = interval
        self.append(SatInterval(last_interval.xmax, None, prev))

    @property
    def begin(self) -> float:
        return self[0].begin

    @property
    def end(self) -> float:
        # This is slightly counter intuitive, but the last interval is infact
        # empty and only represents the final boundary. So its begin is 
        # the final boundary.
        return self[-1].begin

    @property
    def is_point_tier(self) -> bool:
        return False


class SatGrid(OrderedDict):
    """TextGrid representation to enable editing with GUI."""

    def __init__(self, textgrid: TextGrid) -> None:
        for tier_name in textgrid:
            self[tier_name] = SatTier(textgrid[tier_name])
    
    def as_textgrid(self):
        pass

    @property
    def begin(self) -> float:
        key = self.keys()[0]
        return self[key].begin

    @property
    def end(self) -> float:
        key = self.keys()[0]
        return self[key].end
        
    def format_long(self) -> str:
        '''Format self as long format TextGrid.'''
        global long_header, long_tier, long_point, long_interval
        out = long_header.format(self.xmin, self.xmax, len(self))
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
                                    len(tier))
            for elem_count, elem in enumerate(tier, 1):
                if tier.is_point_tier:
                    out += long_point.format(elem_count,
                                             elem.xpos,
                                             elem.text)
                elif elem.next:
                    out += long_interval.format(elem_count,
                                                elem.begin,
                                                elem.next.begin,
                                                elem.text)
                else:
                    # The last interval does not contain anything.
                    # It only marks the end of the file and final 
                    # interval's end. That info got already used by
                    # elem.next.begin above.
                    pass
        return out

class AnnotationBoundary:
    """
    Draggable boundary with blitting.
    
    This class copies its core functionality from the
    matplotlib draggable rectangles example.
    """

    lock = None  # only one can be animated at a time

    def __init__(self, lines, annotation=None):
        self.lines = lines
        self.annotation = annotation
        self.press = None
        self.backgrounds = []

    def connect(self):
        """Connect to all the events we need."""
        for line in self.lines:
            self.cidpress = line.figure.canvas.mpl_connect(
                'button_press_event', self.on_press)
            self.cidrelease = line.figure.canvas.mpl_connect(
                'button_release_event', self.on_release)
            self.cidmotion = line.figure.canvas.mpl_connect(
                'motion_notify_event', self.on_motion)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        if AnnotationBoundary.lock is not None:
            return

        is_inaxes = False
        for line in self.lines:
            if (event.inaxes == line.axes):
                is_inaxes = True
        if not is_inaxes:
            return

        some_line_contains = False
        for line in self.lines:
            contains, attrd = line.contains(event)
            if contains:
                some_line_contains = True
                break
        if not some_line_contains:
            return

        self.press = line.get_data(), (event.xdata, event.ydata)
        AnnotationBoundary.lock = self

        # draw everything but the selected line and store the pixel buffer
        for line in self.lines:
            canvas = line.figure.canvas
            axes = line.axes
            line.set_animated(True)
            canvas.draw()
            self.backgrounds.append(canvas.copy_from_bbox(line.axes.bbox))

            # now redraw just the line
            axes.draw_artist(line)

            # and blit just the redrawn area
            canvas.blit(axes.bbox)

    def on_motion(self, event):
        """Move the rectangle if the mouse is over us."""
        if AnnotationBoundary.lock is not self:
            return

        is_inaxes = False
        for line in self.lines:
            if (event.inaxes == line.axes):
                is_inaxes = True
        if not is_inaxes:
            return

        (x0, y0), (xpress, ypress) = self.press
        dx = event.xdata - xpress
        for i, line in enumerate(self.lines):
            line.set(xdata=x0+dx)

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
        if AnnotationBoundary.lock is not self:
            return

        self.press = None
        AnnotationBoundary.lock = None

        # turn off the rect animation property and reset the background
        for line in self.lines:
            line.set_animated(False)
            # redraw the full figure
            line.figure.canvas.draw()

        self.backgrounds = []

    def disconnect(self):
        """Disconnect all callbacks."""
        for line in self.lines:
            line.figure.canvas.mpl_disconnect(self.cidpress)
            line.figure.canvas.mpl_disconnect(self.cidrelease)
            line.figure.canvas.mpl_disconnect(self.cidmotion)

# fig, ax = plt.subplots()
# lines = []
# drs = []
# for value in 20*np.random.rand(10):
#     line = ax.axvline(value)
#     lines.append(line)
#     dr = AnnotationBoundary(line)
#     dr.connect()
#     drs.append(dr)

# plt.show()