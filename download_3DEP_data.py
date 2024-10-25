'''
Download some specific high-resolution LIDAR-derived DEM data files for Florida from the 3-D Elevation Program (3DEP).
A wrapper for command-line wget commands.

Usage:
python download_3DEP_data.py

Warning:
Each tile is large so the full output is very large.
'''

import os
import subprocess

# Base URL format
base_url = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/FL_Peninsular_FDEM_2018_D19_DRRA/TIFF/USGS_1M_17_x{xtile}y{ytile}_FL_Peninsular_FDEM_2018_D19_DRRA.tif"

# Local directory to store files
download_dir = "./output_3DEP_tiles"

# Create download directory if it doesn't exist
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 
# Port Charlotte: (x, y) = (39, 299) 
# Sarasota: (x, y) = (34, 303)
# Loop over x- and y-tiles
x_tile_range = (33, 40)
y_tile_range = (299, 304)
for x_tile in range(*x_tile_range):
    for y_tile in range(*y_tile_range):
        # Construct file name
        file_name = f"USGS_1M_17_x{x_tile}y{y_tile}_FL_Peninsular_FDEM_2018_D19_DRRA.tif"
        file_path = os.path.join(download_dir, file_name)

        # Check if the file already exists locally
        if os.path.exists(file_path):
            print(f"File {file_name} already exists, skipping download.")
        else:
            # Construct the full URL
            file_url = base_url.format(xtile=x_tile, ytile=y_tile)
            
            # Use wget to download the file
            try:
                print(f"Downloading {file_name} from {file_url}...")
                subprocess.run(["wget", "-O", file_path, file_url, "--show-progress"], check=True)
                print(f"Downloaded {file_name}.")
            except subprocess.CalledProcessError:
                print(f"Failed to download {file_name} from {file_url}.")
