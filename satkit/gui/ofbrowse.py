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


import pickle
import os

# numpy and scipy
import numpy as np

# scientific plotting
import matplotlib.pyplot as plt
import scipy
from scipy import integrate
from scipy.stats import trim_mean

class GUI:
    def __init__(self, data):
        """ class initializer """
        # store relevant dictionary entries into convenient local variables
        self.ultra_interp = data['ultra_interp']
        self.ofdisp = data['ofdisp']
        self.ult_no_frames = data['ult_no_frames']
        self.ult_time = data['ult_time']
        self.ult_period = self.ult_time[1] - self.ult_time[0]

        # TODO implement vector scaling as a user parameter
        self.scaling = 1.0

        # visualize registration as quiver plot
        # TODO implement index skipping to thin the visualization of the field (and eventually make this an option for the user)
        self.xx, self.yy = np.meshgrid(range(1, self.ultra_interp[0].shape[0]),
                                       range(1, self.ultra_interp[0].shape[1]))

        #TODO set the default figure size to be some sensible proportion of the screen real estate
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_axes([0.1, 0.6, 0.4, 0.4])
        self.im = self.ax.imshow(self.ultra_interp[0])
        self.quiver = plt.quiver(self.yy, self.xx,
                                 self.ofdisp[0]['of'].forward[:, :, 0],
                                 self.ofdisp[0]['of'].forward[:, :, 1],
                                 scale_units='x', scale=10.0, color='r')

        # compute the velocity and position using the trimmed mean approach
        self.vel = np.empty((self.ult_no_frames - 1, 2))
        self.pos = np.empty((self.ult_no_frames - 2, 2))
        self.compute_kinematics()

        # TODO give user control over axis scaling, analysis direction (vertical or horizontal), and sign of the data
        # create velocity plot
        self.ax_vel = self.fig.add_axes([0.1, 0.5, 0.8, 0.1])
        self.ax_vel.set_xlim([0.0, self.ult_time[-1]])
        self.ax_vel.set_ylim([-1e3, 1e3])
        self.ax_vel.set_title("Velocity (Horizontal)")
        self.ax_vel.set_ylabel("velocity (mm/s)")
        self.ax_vel.tick_params(bottom=False)

        self.line_vel = plt.plot(self.ult_time[0:self.ult_no_frames - 1], self.vel[:, 1])
        self.point_vel, = plt.plot(self.ult_time[0], self.vel[0, 1], marker="o", ls="", color="r")
        plt.axhline(linewidth=2, color='k')

        # create position plot
        self.ax_pos = self.fig.add_axes([0.1, 0.3, 0.8, 0.1])
        self.ax_pos.set_xlim([0.0, self.ult_time[-1]])
        self.ax_pos.set_ylim([-1e2, 1e2])
        self.ax_pos.set_title("Position (Horizontal)")
        self.ax_pos.set_ylabel("relative position (mm)")
        self.ax_pos.set_xlabel("time (s)")

        self.line_pos = plt.plot(self.ult_time[1:self.ult_no_frames - 1], self.pos[:, 1])
        self.point_pos, = plt.plot(self.ult_time[0], self.pos[0, 1], marker="o", ls="", color="r")
        plt.axhline(linewidth=2, color='k')

        # create audio plot
        self.ax_audio = self.fig.add_axes([0.1, 0.1, 0.8, 0.1])

        self.frame_index = 0

        # connect the callbacks
        self.cid_scroll = self.fig.canvas.mpl_connect('scroll_event', self.mouse_scroll)

        plt.show()

    def mouse_scroll(self, event):
        """ create mousewheel callback function for updating the plot to a new frame """
        # detect the mouse wheel action
        if event.button == 'up':
            self.frame_index = min(self.frame_index + 1, self.ult_no_frames - 2)
        elif event.button == 'down':
            self.frame_index = max(self.frame_index - 1, 0)
        else:
            print("oops")
            
        # update the gui
        self.update_gui()

    def update_gui(self):
        """ update the gui by changing the state according to the current frame """
        # update the plot
        self.im.set_data(self.ultra_interp[self.frame_index])
        self.quiver.set_UVC(self.ofdisp[self.frame_index]['of'].forward[:, :, 0],
                            self.ofdisp[self.frame_index]['of'].forward[:, :, 1])

        # TODO point updating not plotting correctly --- some sort of scaling issue?
        # TODO produces index out of bounds error at upper end of frames
        self.point_vel.set_xdata(self.ult_time[self.frame_index])
        self.point_vel.set_ydata(self.vel[self.frame_index, 0])

        self.point_pos.set_xdata(self.ult_time[self.frame_index])
        self.point_pos.set_ydata(self.pos[self.frame_index, 0])

        self.ax.set_title(str(self.frame_index))
        self.fig.canvas.draw_idle()

    def compute_kinematics(self):
        """ compute the velocity and position from the displacement field """

        # TODO implement alternative means of obtaining the consensus vector
        # TODO this is working differently from the Matlab implementation (may need padding of the signals, e.g., following integration)
        # obtain the consensus velocity vector for each frame(pair)
        for fIdx in range(0, self.ult_no_frames - 1):
            disp_comp_v = self.ofdisp[fIdx]['of'].forward[:, :, 0]
            disp_comp_h = self.ofdisp[fIdx]['of'].forward[:, :, 1]

            self.vel[fIdx, 0] = trim_mean(disp_comp_h.flatten(), 0.25) / self.ult_period * self.scaling
            self.vel[fIdx, 1] = trim_mean(disp_comp_v.flatten(), 0.25) / self.ult_period * self.scaling

        # perform numerical integration
        self.pos[:, 0] = integrate.cumtrapz(self.vel[:, 0], self.ult_time[0:self.ult_no_frames - 1])
        self.pos[:, 1] = integrate.cumtrapz(self.vel[:, 1], self.ult_time[0:self.ult_no_frames - 1])


def main():
    # TODO hard coded path for convenience while developing code
    filename = "..\\results\\P1_01_OF.pickle"

    # unpickle an OF file produced by ofreg.py
    data = pickle.load(open(filename, "rb"))

    # create the ofbrowse gui (scaffolded on Matplotlib)
    gd = GUI(data)

if __name__ == '__main__':
    main()
