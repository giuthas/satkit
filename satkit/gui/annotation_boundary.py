
# Draggable boundary with blitting.
import matplotlib.pyplot as plt
import numpy as np


class AnnotationBoundary:
    lock = None  # only one can be animated at a time

    def __init__(self, line):
        self.line = line
        self.press = None
        self.background = None

    def connect(self):
        """Connect to all the events we need."""
        self.cidpress = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        """Check whether mouse is over us; if so, store some data."""
        if (event.inaxes != self.line.axes
                or AnnotationBoundary.lock is not None):
            return
        contains, attrd = self.line.contains(event)
        if not contains:
            return
        print('event contains', self.line.get_data())
        self.press = self.line.get_data(), (event.xdata, event.ydata)
        AnnotationBoundary.lock = self

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.line.figure.canvas
        axes = self.line.axes
        self.line.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.line.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.line)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        """Move the rectangle if the mouse is over us."""
        if (event.inaxes != self.line.axes
                or AnnotationBoundary.lock is not self):
            return
        (x0, y0), (xpress, ypress) = self.press
        dx = event.xdata - xpress
        self.line.set(xdata=x0+dx)

        canvas = self.line.figure.canvas
        axes = self.line.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.line)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_release(self, event):
        """Clear button press information."""
        if AnnotationBoundary.lock is not self:
            return

        self.press = None
        AnnotationBoundary.lock = None

        # turn off the rect animation property and reset the background
        self.line.set_animated(False)
        self.background = None

        # redraw the full figure
        self.line.figure.canvas.draw()

    def disconnect(self):
        """Disconnect all callbacks."""
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)

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
