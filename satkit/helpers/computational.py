import numpy as np


def combine_coordinates(c1: np.ndarray, c2: np.ndarray) -> np.ndarray:
    """
    Concatenate the given coordinates by rows.

    Parameters
    ----------
    c1 : np.ndarray
        data for first row. Has to be same length as c2.
    c2 : np.ndarray
        data for second row. Has to be same length as c1.

    Returns
    -------
    np.ndarray
        The concatenation result: an array with 
        shape = ([c1 and c2 length], 2).
    """
    return np.concatenate((c1.reshape(-1, 1), c2.reshape(-1, 1)), axis=1)


def cartesian_to_polar(xy_array: np.ndarray) -> np.ndarray:
    """
    Transform an array of 2D Cartesian coordinates to polar coordinates.

    Parameters
    ----------
    xy_array : np.ndarray
        x and y values in their own rows.

    Returns
    -------
    np.ndarray
        r and phi values in their own rows.
    """
    r = np.sqrt((xy_array**2).sum(1))
    phi = np.arctan2(xy_array[:, 1], xy_array[:, 0])
    return combine_coordinates(r, phi)


def polar_to_cartesian(r_phi_array: np.ndarray) -> np.ndarray:
    """
    Transform an array of 2D polar coordinates to Cartesian coordinates.

    Parameters
    ----------
    r_phi_array : np.ndarray
        r and phi values in their own rows.

    Returns
    -------
    np.ndarray
        x and y values in their own rows.
    """
    x = r_phi_array[:, 0] * np.cos(r_phi_array[:, 1])
    y = r_phi_array[:, 0] * np.sin(r_phi_array[:, 1])
    return combine_coordinates(x, y)
