'''
Downloads MCDWD flood data for a specified day.
A wrapper for command-line wget commands.
You will need an authentication key.
Usage:

python3 download_MCDWD_flood_data.py
'''
import argparse
from datetime import datetime, timedelta
import subprocess

def get_day_of_year(date_input):
    # If 'today' is provided, use today's date
    if date_input == 'today':
        date_obj = datetime.today()
    elif date_input == 'yesterday':
        date_obj = datetime.today()
        date_obj = date_obj - timedelta(days=1)
    else:
        try:
            # Try to parse the date string (YYYY-MM-DD)
            date_obj = datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            raise argparse.ArgumentTypeError("Invalid date format '{:}'. Please use YYYY-MM-DD or 'today' or 'yesterday'.".format(date_input))
    
    # Convert the date object to the day of the year
    year = date_obj.year
    day_of_year = date_obj.timetuple().tm_yday
    return year, day_of_year

def main():
    '''
    Bulk download instructions here:
    https://nrt3.modaps.eosdis.nasa.gov/help/downloads

    ChatGPT explanation of the example wget command
    wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=4 "https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/6/MOD09/2018/143/" --header "Authorization: Bearer ABCDEFGH-12345-IJKL-6789-MNOPQRST" -P /Users/jdoe/data

        wget: A command-line utility to download files from the web.

        -e robots=off: This tells wget to ignore the robots.txt file. The robots.txt file is a web standard that specifies how search engines and other automated bots should crawl a site. By default, wget follows robots.txt, but with this option, it will ignore it.
        
        -m: This activates the mirror option. It enables recursive downloading with time-stamping, which makes the downloaded content similar to a local copy of the remote directory.
        
        -np: This stands for no-parent. It ensures that wget does not traverse up to the parent directories. In this case, wget will not go above the https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/6/MOD09/2018/143/ directory.
        
        -R .html,.tmp: The reject option. It tells wget to exclude downloading files with .html and .tmp extensions. It only downloads files that don't have these extensions.
        
        -nH: This disables creating a directory for the remote host. Normally, wget creates a directory structure starting with the hostname, but this option prevents it from doing so.
        
        --cut-dirs=4: This removes (or "cuts") the first 4 directory levels from the URL when saving files locally. Given the URL:
        
        https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/6/MOD09/2018/143/
        
        The first 4 directories (/api/v2/content/archives/) will be stripped, and the files will be stored under /allData/6/MOD09/2018/143/.
        
        "https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/6/MOD09/2018/143/": This is the target URL from which files will be downloaded.
        
        --header "Authorization: Bearer ABCDEFGH-12345-IJKL-6789-MNOPQRST": This adds an HTTP header with the Authorization Bearer token, which is required for authentication. In this case, the token (ABCDEFGH-12345-IJKL-6789-MNOPQRST) provides access to the NASA API endpoint.
        
        -P /Users/jdoe/data: This specifies the local directory to save the downloaded files. In this case, files will be saved under /Users/jdoe/data.
    '''

    # Define paths.
    dir_output = '/Users/hrmd/Documents/work/map_action/2024-001-usa/MCDWD_downloads'
    path_bearer_token = 'earthdata_bearer_token_hrmd.txt'

    # Read bearer token.
    with open(path_bearer_token, 'r') as in_id:

        bearer_token_str = in_id.readline().strip()

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Parse arguments for downloading MCDWD flood data.")
    parser.add_argument("date", type=str, help="Date string in format YYYY-MM-DD or 'today' for the current date or 'yesterday' for the yesterday's date.")
    
    # Parse the command-line arguments
    args = parser.parse_args()
    year, day_of_year = get_day_of_year(args.date)

    # Define target tiles ('granules').
    # See the 'tile map' image on this page:
    # https://www.earthdata.nasa.gov/learn/find-data/near-real-time/modis-nrt-global-flood-product
    tiles = [[8, 5], [8, 6], [9, 5], [9, 6], [10, 5], [10, 6]] 

    # Define target datasets.
    datasets = ['1', '1C', '2', '3']

    #wget -e robots=off -r -np -R .html,.tmp -A "*h00v01*.tif,*h01v02*.tif,*h02v02*.tif" -nH --cut-dirs=4 "https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/6/MOD09/2018/143/" --header "Authorization: Bearer ABCDEFGH-12345-IJKL-6789-MNOPQRST" -P /Users/jdoe/data
    cmd_fmt = 'wget -e robots=off -r -np -R .html,.tmp -A "{:}" -nH --cut-dirs=6 "{:}" --header "Authorization: Bearer {:}" -P {:}'

    # Loop over tiles and datasets and define the target URL.
    #https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/61/MCDWD_L3_F1_NRT/2024/275/MCDWD_L3_F1_NRT.A2024275.h00v01.061.2024275052248.tif
    #url_folder_fmt = 'https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/61/MCDWD_L3_F{:}_NRT/{:04d}/{:03d}/MCDWD_L3_F{:}_NRT.A{:04d}{:03d}.h{:02d}v{:02d}.061.{:04d}{:03d}*.tif'
    url_folder_fmt = 'https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/61/MCDWD_L3_F{:}_NRT/{:04d}/{:03d}/'
    #url_file_fmt = 'MCDWD_L3_F{:}_NRT.A{:04d}{:03d}.h{:02d}v{:02d}.061.{:04d}{:03d}*.tif'
    url_file_fmt = '*h{:02d}v{:02d}*.tif'
    for dataset in datasets:
        
        url_folder = url_folder_fmt.format(dataset, year, day_of_year)

        url_file_list = []
        for tile in tiles:
            
            h, v = tile
            #url_file = url_file_fmt.format(dataset, year, day_of_year, h, v, year, day_of_year)
            url_file = url_file_fmt.format(h, v)
            url_file_list.append(url_file)
           
        url_file_list_str = ','.join(url_file_list)

        cmd = cmd_fmt.format(url_file_list_str, url_folder, bearer_token_str, dir_output)

        print('\n', 80*'-', cmd)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        print('\n')
   
    return

if __name__ == '__main__':

    main()
