# Return instructions for how to run SATKIT
./satkit.py

# Run with the default configuration and show 10 recordings in the
# GUI. 
#   - Just files, nothing fancy.
./satkit.py tongue_data_1_1/

#   - Missing files
./satkit.py tongue_data_1_2/

#   - Missing files, exclusion list
./satkit.py tongue_data_1_2/ -e tongue_data_1_2/exclusion_list.csv
