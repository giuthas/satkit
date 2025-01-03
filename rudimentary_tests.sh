##
## Copyright (c) 2019-2024
## Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
##
## This file is part of Speech Articulation ToolKIT
## (see https://github.com/giuthas/satkit/).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##
## The example data packaged with this program is licensed under the
## Creative Commons Attribution-NonCommercial-ShareAlike 4.0
## International (CC BY-NC-SA 4.0) License. You should have received a
## copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
## International (CC BY-NC-SA 4.0) License along with the data. If not,
## see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
##
## When using the toolkit for scientific publications, please cite the
## articles listed in README.markdown. They can also be found in
## citations.bib in BibTeX format.
##

# Return instructions for how to run SATKIT
./satkit.py

# Run with the default configuration and show 10 recordings in the
# GUI. 
#   - Just files, nothing fancy.
./satkit.py recorded_data/tongue_data_1_1/
# The same but in interactive interpreter mode
./satkit_interactive.py recorded_data/tongue_data_1_1/

#   - Missing files
./satkit.py recorded_data/tongue_data_1_2/

#   - Missing files, exclusion list in .csv format
./satkit.py recorded_data/tongue_data_1_2/ -e recorded_data/tongue_data_1_2/exclusion_list.csv

#   - Missing files, exclusion list in .yaml format
./satkit.py recorded_data/tongue_data_1_2/ -e recorded_data/tongue_data_1_2/exclusion_list.yaml
