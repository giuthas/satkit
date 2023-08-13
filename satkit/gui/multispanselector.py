import numpy as np
from matplotlib import _api, backend_tools, cbook
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.widgets import ToolLineHandles, _SelectorWidget


class MultiSpanSelector(_SelectorWidget):
    """
    Visually select a min/max range on a multiple axes and call a function with
    those values.

    To guarantee that the selector remains responsive, keep a reference to it.

    In order to turn off the SpanSelector, set ``span_selector.active`` to
    False.  To turn it back on, set it to True.

    Press and release events triggered at the same coordinates outside the
    selection will clear the selector, except when
    ``ignore_event_outside=True``.

    This implementation is directly based on matplotlib's SpanSelector.

    Parameters
    ----------
    axes : array of `matplotlib.axes.Axes`

    onselect : callable
        A callback function that is called after a release event and the
        selection is created, changed or removed.
        It must have the signature::

            def on_select(min: float, max: float) -> Any

    direction : {"horizontal", "vertical"}
        The direction along which to draw the span selector.

    minspan : float, default: 0
        If selection is less than or equal to *minspan*, the selection is
        removed (when already existing) or cancelled.

    useblit : bool, default: False
        If True, use the backend-dependent blitting features for faster
        canvas updates. See the tutorial :doc:`/tutorials/advanced/blitting`
        for details.

    props : dict, optional
        Dictionary of `matplotlib.patches.Patch` properties.
        Default:

            ``dict(facecolor='red', alpha=0.5)``

    onmove_callback : func(min, max), min/max are floats, default: None
        Called on mouse move while the span is being selected.

    interactive : bool, default: False
        Whether to draw a set of handles that allow interaction with the
        widget after it is drawn.

    button : `.MouseButton` or list of `.MouseButton`, default: all buttons
        The mouse buttons which activate the span selector.

    handle_props : dict, default: None
        Properties of the handle lines at the edges of the span. Only used
        when *interactive* is True. See `matplotlib.lines.Line2D` for valid
        properties.

    grab_range : float, default: 10
        Distance in pixels within which the interactive tool handles can be
        activated.

    state_modifier_keys : dict, optional
        Keyboard modifiers which affect the widget's behavior.  Values
        amend the defaults, which are:

        - "clear": Clear the current shape, default: "escape".

    drag_from_anywhere : bool, default: False
        If `True`, the widget can be moved by clicking anywhere within
        its bounds.

    ignore_event_outside : bool, default: False
        If `True`, the event triggered outside the span selector will be
        ignored.

    snap_values : 1D array-like, optional
        Snap the selector edges to the given values.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import matplotlib.widgets as mwidgets
    >>> fig, ax = plt.subplots()
    >>> ax.plot([1, 2, 3], [10, 50, 100])
    >>> def onselect(vmin, vmax):
    ...     print(vmin, vmax)
    >>> span = mwidgets.SpanSelector(ax, onselect, 'horizontal',
    ...                              props=dict(facecolor='blue', alpha=0.5))
    >>> fig.show()

    See also: :doc:`/gallery/widgets/span_selector`
    """

    def __init__(self, axes, onselect, direction, minspan=0, useblit=False,
                 props=None, onmove_callback=None, interactive=False,
                 button=None, handle_props=None, grab_range=10,
                 state_modifier_keys=None, drag_from_anywhere=False,
                 ignore_event_outside=False, snap_values=None):

        if state_modifier_keys is None:
            state_modifier_keys = dict(clear='escape',
                                       square='not-applicable',
                                       center='not-applicable',
                                       rotate='not-applicable')
        super().__init__(ax, onselect, useblit=useblit, button=button,
                         state_modifier_keys=state_modifier_keys)

        if props is None:
            props = dict(facecolor='red', alpha=0.5)

        props['animated'] = self.useblit

        self.direction = direction
        self._extents_on_press = None
        self.snap_values = snap_values

        # self._pressv is deprecated and we don't use it internally anymore
        # but we maintain it until it is removed
        self._pressv = None

        self._props = props
        self.onmove_callback = onmove_callback
        self.minspan = minspan

        self.grab_range = grab_range
        self._interactive = interactive
        self._edge_handles = None
        self.drag_from_anywhere = drag_from_anywhere
        self.ignore_event_outside = ignore_event_outside

        # Reset canvas so that `new_axes` connects events.
        self.canvas = None
        self.new_axes(ax)

        # Setup handles
        self._handle_props = {
            'color': props.get('facecolor', 'r'),
            **cbook.normalize_kwargs(handle_props, Line2D)}

        if self._interactive:
            self._edge_order = ['min', 'max']
            self._setup_edge_handles(self._handle_props)

        self._active_handle = None

        # prev attribute is deprecated but we still need to maintain it
        self._prev = (0, 0)

    def new_axes(self, ax):
        """Set SpanSelector to operate on a new Axes."""
        self.ax = ax
        if self.canvas is not ax.figure.canvas:
            if self.canvas is not None:
                self.disconnect_events()

            self.canvas = ax.figure.canvas
            self.connect_default_events()

        # Reset
        self._selection_completed = False

        if self.direction == 'horizontal':
            trans = ax.get_xaxis_transform()
            w, h = 0, 1
        else:
            trans = ax.get_yaxis_transform()
            w, h = 1, 0
        rect_artist = Rectangle((0, 0), w, h,
                                transform=trans,
                                visible=False,
                                **self._props)

        self.ax.add_patch(rect_artist)
        self._selection_artist = rect_artist

    def _setup_edge_handles(self, props):
        # Define initial position using the axis bounds to keep the same bounds
        if self.direction == 'horizontal':
            positions = self.ax.get_xbound()
        else:
            positions = self.ax.get_ybound()
        self._edge_handles = ToolLineHandles(self.ax, positions,
                                             direction=self.direction,
                                             line_props=props,
                                             useblit=self.useblit)

    @property
    def _handles_artists(self):
        if self._edge_handles is not None:
            return self._edge_handles.artists
        else:
            return ()

    def _set_cursor(self, enabled):
        """Update the canvas cursor based on direction of the selector."""
        if enabled:
            cursor = (backend_tools.Cursors.RESIZE_HORIZONTAL
                      if self.direction == 'horizontal' else
                      backend_tools.Cursors.RESIZE_VERTICAL)
        else:
            cursor = backend_tools.Cursors.POINTER

        self.ax.figure.canvas.set_cursor(cursor)

    def connect_default_events(self):
        # docstring inherited
        super().connect_default_events()
        if getattr(self, '_interactive', False):
            self.connect_event('motion_notify_event', self._hover)

    def _press(self, event):
        """Button press event handler."""
        self._set_cursor(True)
        if self._interactive and self._selection_artist.get_visible():
            self._set_active_handle(event)
        else:
            self._active_handle = None

        if self._active_handle is None or not self._interactive:
            # Clear previous rectangle before drawing new rectangle.
            self.update()

        v = event.xdata if self.direction == 'horizontal' else event.ydata
        # self._pressv and self._prev are deprecated but we still need to
        # maintain them
        self._pressv = v
        self._prev = self._get_data(event)

        if self._active_handle is None and not self.ignore_event_outside:
            # when the press event outside the span, we initially set the
            # visibility to False and extents to (v, v)
            # update will be called when setting the extents
            self._visible = False
            self.extents = v, v
            # We need to set the visibility back, so the span selector will be
            # drawn when necessary (span width > 0)
            self._visible = True
        else:
            self.set_visible(True)

        return False

    @property
    def direction(self):
        """Direction of the span selector: 'vertical' or 'horizontal'."""
        return self._direction

    @direction.setter
    def direction(self, direction):
        """Set the direction of the span selector."""
        _api.check_in_list(['horizontal', 'vertical'], direction=direction)
        if hasattr(self, '_direction') and direction != self._direction:
            # remove previous artists
            self._selection_artist.remove()
            if self._interactive:
                self._edge_handles.remove()
            self._direction = direction
            self.new_axes(self.ax)
            if self._interactive:
                self._setup_edge_handles(self._handle_props)
        else:
            self._direction = direction

    def _release(self, event):
        """Button release event handler."""
        self._set_cursor(False)
        # self._pressv is deprecated but we still need to maintain it
        self._pressv = None

        if not self._interactive:
            self._selection_artist.set_visible(False)

        if (self._active_handle is None and self._selection_completed and
                self.ignore_event_outside):
            return

        vmin, vmax = self.extents
        span = vmax - vmin

        if span <= self.minspan:
            # Remove span and set self._selection_completed = False
            self.set_visible(False)
            if self._selection_completed:
                # Call onselect, only when the span is already existing
                self.onselect(vmin, vmax)
            self._selection_completed = False
        else:
            self.onselect(vmin, vmax)
            self._selection_completed = True

        self.update()

        self._active_handle = None

        return False

    def _hover(self, event):
        """Update the canvas cursor if it's over a handle."""
        if self.ignore(event):
            return

        if self._active_handle is not None or not self._selection_completed:
            # Do nothing if button is pressed and a handle is active, which may
            # occur with drag_from_anywhere=True.
            # Do nothing if selection is not completed, which occurs when
            # a selector has been cleared
            return

        _, e_dist = self._edge_handles.closest(event.x, event.y)
        self._set_cursor(e_dist <= self.grab_range)

    def _onmove(self, event):
        """Motion notify event handler."""

        # self._prev are deprecated but we still need to maintain it
        self._prev = self._get_data(event)

        v = event.xdata if self.direction == 'horizontal' else event.ydata
        if self.direction == 'horizontal':
            vpress = self._eventpress.xdata
        else:
            vpress = self._eventpress.ydata

        # move existing span
        # When "dragging from anywhere", `self._active_handle` is set to 'C'
        # (match notation used in the RectangleSelector)
        if self._active_handle == 'C' and self._extents_on_press is not None:
            vmin, vmax = self._extents_on_press
            dv = v - vpress
            vmin += dv
            vmax += dv

        # resize an existing shape
        elif self._active_handle and self._active_handle != 'C':
            vmin, vmax = self._extents_on_press
            if self._active_handle == 'min':
                vmin = v
            else:
                vmax = v
        # new shape
        else:
            # Don't create a new span if there is already one when
            # ignore_event_outside=True
            if self.ignore_event_outside and self._selection_completed:
                return
            vmin, vmax = vpress, v
            if vmin > vmax:
                vmin, vmax = vmax, vmin

        self.extents = vmin, vmax

        if self.onmove_callback is not None:
            self.onmove_callback(vmin, vmax)

        return False

    def _draw_shape(self, vmin, vmax):
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if self.direction == 'horizontal':
            self._selection_artist.set_x(vmin)
            self._selection_artist.set_width(vmax - vmin)
        else:
            self._selection_artist.set_y(vmin)
            self._selection_artist.set_height(vmax - vmin)

    def _set_active_handle(self, event):
        """Set active handle based on the location of the mouse event."""
        # Note: event.xdata/ydata in data coordinates, event.x/y in pixels
        e_idx, e_dist = self._edge_handles.closest(event.x, event.y)

        # Prioritise center handle over other handles
        # Use 'C' to match the notation used in the RectangleSelector
        if 'move' in self._state:
            self._active_handle = 'C'
        elif e_dist > self.grab_range:
            # Not close to any handles
            self._active_handle = None
            if self.drag_from_anywhere and self._contains(event):
                # Check if we've clicked inside the region
                self._active_handle = 'C'
                self._extents_on_press = self.extents
            else:
                self._active_handle = None
                return
        else:
            # Closest to an edge handle
            self._active_handle = self._edge_order[e_idx]

        # Save coordinates of rectangle at the start of handle movement.
        self._extents_on_press = self.extents

    def _contains(self, event):
        """Return True if event is within the patch."""
        return self._selection_artist.contains(event, radius=0)[0]

    @staticmethod
    def _snap(values, snap_values):
        """Snap values to a given array values (snap_values)."""
        # take into account machine precision
        eps = np.min(np.abs(np.diff(snap_values))) * 1e-12
        return tuple(
            snap_values[np.abs(snap_values - v + np.sign(v) * eps).argmin()]
            for v in values)

    @property
    def extents(self):
        """Return extents of the span selector."""
        if self.direction == 'horizontal':
            vmin = self._selection_artist.get_x()
            vmax = vmin + self._selection_artist.get_width()
        else:
            vmin = self._selection_artist.get_y()
            vmax = vmin + self._selection_artist.get_height()
        return vmin, vmax

    @extents.setter
    def extents(self, extents):
        # Update displayed shape
        if self.snap_values is not None:
            extents = tuple(self._snap(extents, self.snap_values))
        self._draw_shape(*extents)
        if self._interactive:
            # Update displayed handles
            self._edge_handles.set_data(self.extents)
        self.set_visible(self._visible)
        self.update()
