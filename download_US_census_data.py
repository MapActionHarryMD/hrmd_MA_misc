# Imports: Standard library.
import csv
import json
import os
import requests

# Imports: Third party.
import pandas as pd

# Define global variables.
dir_output = 'output'

def load_api_from_txt_file(filename='api_key_US_census.txt'):
    with open(filename, 'r') as file:
        api_key = file.read().strip()
    return api_key

# Usage
api_key = read_api_key()
print(api_key)


def define_headers():
    '''
    'headers' are human-readable column headers (10 chars or shorter) for output CSV files.
    'keys' are string codes used in the US Census Data to indicate specific variables.
    Each 'header' has an associated 'key', e.g.
        male population age 0-4 has key 'B01001_003E' and header 'pM_000_004'.

    Definitions are for 2021 ACS data (https://api.census.gov/data/2021/acs/acs5)
    I haven’t found a good source of documentation yet, but I believe the following codes apply:

    B01001_001E: Total Population

    B01001_002E: Total Male Population
    B01001_003E: Male under 5 years
    B01001_004E: Male 5 to 9 years
    ...
    B01001_025E: Male 85 years and over.

    B01001_026E: Total Female Population
    B01001_027E: Female under 5 years
    B01001_028E: Female 5 to 9 years
    ...
    B01001_049E: Female 85 years and over.
    '''
    
    # Based on https://api.census.gov/data/2019/acs/acs1/groups/B01001.html
    age_brackets = [
        0, 5, 10, 15, 18, 20, 21, 22, 25, 30, 35, 40, 45, 50, 55, 60, 62, 65, 67, 70,
        75, 80, 85, 99,
            ]

    # Generate a list human-readable column headers.
    # (Try to keep 10 chars or less because I think shapefiles need that.)
    pop_str = 'p'
    headers = ['{:}'.format(pop_str)]
    #n_age_brackets = 23
    n_age_brackets = len(age_brackets) - 1
    for gender in ['M', 'F']:

        header = '{:}{:}'.format(pop_str, gender)
        headers.append(header)

        for i in range(n_age_brackets):
            # lo = i * 5
            # hi = lo + 4
            lo = age_brackets[i]
            hi = age_brackets[i + 1] - 1
            header = '{:}{:}_{:02d}_{:02d}'.format(pop_str, gender, lo, hi)
            if i == (n_age_brackets - 1):
                header = header[:-3]
                header = header + 'pls'

            headers.append(header)
    
    # Get census API query values corresponding to the headers.
    fmt = 'B01001_{:03d}E'
    keys = []
    for i, header in enumerate(headers):

        key = fmt.format(i + 1)
        keys.append(key)
    
    # The place name is a special key.
    headers.append('name')
    keys.append('NAME')

    for key, header in zip(keys, headers):

        print(key, header)

    return keys, headers

def define_US_state_name_to_FIPS_code_dict():

    US_state_name_to_FIPS_code_dict = {
        'Alabama': 1,
        'Alaska': 2,
        'Arizona': 4,
        'Arkansas': 5,
        'California': 6,
        'Colorado': 8,
        'Connecticut': 9,
        'Delaware': 10,
        'Florida': 12,
        'Georgia': 13,
        'Hawaii': 15,
        'Idaho': 16,
        'Illinois': 17,
        'Indiana': 18,
        'Iowa': 19,
        'Kansas': 20,
        'Kentucky': 21,
        'Louisiana': 22,
        'Maine': 23,
        'Maryland': 24,
        'Massachusetts': 25,
        'Michigan': 26,
        'Minnesota': 27,
        'Mississippi': 28,
        'Missouri': 29,
        'Montana': 30,
        'Nebraska': 31,
        'Nevada': 32,
        'New Hampshire': 33,
        'New Jersey': 34,
        'New Mexico': 35,
        'New York': 36,
        'North Carolina': 37,
        'North Dakota': 38,
        'Ohio': 39,
        'Oklahoma': 40,
        'Oregon': 41,
        'Pennsylvania': 42,
        'Rhode Island': 44,
        'South Carolina': 45,
        'South Dakota': 46,
        'Tennessee': 47,
        'Texas': 48,
        'Utah': 49,
        'Vermont': 50,
        'Virginia': 51,
        'Washington': 53,
        'West Virginia': 54,
        'Wisconsin': 55,
        'Wyoming': 56,
        'District of Columbia': 11,
    }

    return US_state_name_to_FIPS_code_dict

def define_target_states_by_FIPS_code(target_states):
    '''
    Define which US states we are interested in.
    '''
    
    US_state_name_to_FIPS_code_dict = define_US_state_name_to_FIPS_code_dict()

    target_states_FIPS_codes = []
    for target_state in target_states:
        
        FIPS_code = US_state_name_to_FIPS_code_dict[target_state]
        target_states_FIPS_codes.append(FIPS_code)

    return target_states_FIPS_codes

def define_admin_level_codes_from_name():
    '''
    Assign an integer admin level to a named admin level.
    '''

    #adm_codes = [ 
    #        'nation',
    #        'region',
    #        'division',
    #        'state',
    #        'county',
    #        'county_subdivision',
    #        'place',
    #        'tract',
    #        'block_group',
    #        'block ',
    #] 

    adm_level_codes_from_name = {
            'county' : 6,
            'place'  : 8,
            }

    return adm_level_codes_from_name

def request_data(api_key, overwrite = False):
    '''
    Formulate and send a GET request to the US census API.
    '''

    # Define US Census API key and endpoint.
    # Endpoint is 2022 ACS5 data, described in first row of this table:
    # https://api.census.gov/data/2022/acs/acs5.html
    # It has disaggregated population data including very small admin levels. 
    # Request an API key here: https://api.census.gov/data/key_signup.html 
    endpoint = "https://api.census.gov/data/2022/acs/acs5"
    
    # Define the "GET" clause of the query, which specifies which variables to
    # download, as a comma-separated list of codes.
    variable_keys, variable_headers = define_headers()
    query_str_GET = ",".join(variable_keys)
    
    # Define which states to download, and get their FIPS code.
    target_states = ['Florida', 'Georgia', 'North Carolina', 'Tennessee']
    target_states_FIPS_codes = define_target_states_by_FIPS_code(target_states)
    
    # Define which admin levels we are interested in. 
    #target_adm_levels = ['county', 'tract']#, 'block group']
    #target_adm_levels = ['county']
    target_adm_levels = ['block group']
    #target_adm_levels = ['block']

    # Also provide a dictionary to map these admin levels to numbers,
    # e.g. county <-> 4.  
    #adm_level_codes_from_name = define_admin_level_codes_from_name()
    
    # Loop over the target admin levels and save the output as separate JSON
    # files. 
    # Store the output paths in a list.
    paths_out = []
    for adm_level in target_adm_levels:

        # Define the output path.
        #adm_code = adm_level_codes_from_name[adm_level]
        #request_name = 'US_pop_by_age_sex__adm{:1d}_{:}'.format(
        #                    adm_code, adm_level)
        request_name = 'US_pop_by_age_sex__{:}'.format(adm_level)
        path_out = os.path.join(dir_output, '{:}.json'.format(request_name))
        path_out = path_out.replace(' ', '_')
        paths_out.append(path_out)

        # Don't overwrite existing files unless requested.
        if os.path.exists(path_out) and not overwrite:

            print("Output file {:} already exists, skipping request.".format(path_out))
            continue

        # Define the "FOR" clause of the query, which specifies the geographic
        # level to look at, e.g. county level.
        # This looks something like: 
        #   county:*
        # which translates as "get data for all counties in the query region".
        query_str_FOR = "{:}:*".format(adm_level),

        # Define the "IN" clause of the query, which specifies the geographic
        # region of the query. In our case, it looks something like
        #   state:12,13
        # where the integers are FIPS codes for the states we are interested in.   
        #if adm_level in ['county', 'tract']:

        query_str_IN = 'state:' + ",".join(['{:02d}'.format(state_FIPS_code) for
                                    state_FIPS_code in target_states_FIPS_codes])

        # For smaller admin levels, IN the query must specify each level of the
        # admin level hierarchy. For example, for block level, we need
        # something like
        #   in=state:12&in=county:*&in=tract:*
        #if adm_level in ['block', 'block group']:
        if adm_level == 'block group':

            query_str_IN = query_str_IN + '&in=county:*&in=tract:*'
            
            #for state_FIPS_code in target_states_FIPS_codes:

            #    query_str_IN = 'state:{:02d}'.format(state_FIPS_code)
            #    query_str_IN_list.append(query_str_IN)

        elif adm_level == 'block':

            query_str_IN = query_str_IN + '&in=county:*&in=tract:*&in=block group:*'

        #else:

        #    raise ValueError('Admin level {:} incorrect or not implemented'.format(adm_level))

        # Store the search parameters in a dictionary. 
        params = {
            "get": query_str_GET,
            "for": query_str_FOR,
            "in" : query_str_IN,
            "key": api_key
        }

        # Make the request.
        print(params)
        print(params['for'])
        response = requests.get(endpoint, params=params)
        print(response)
        print(response.url)
        
        # Convert to JSON.
        data = response.json()

        # Save as a text file.
        print("Writing to {:}".format(path_out))
        with open(path_out, 'w') as file:
            json.dump(data, file)

    return paths_out
    
def convert_json_to_csv(path_json, variable_keys, variable_headers, overwrite = False):

    # Process file path.
    dir_out = os.path.dirname(path_json)
    json_file_name_with_extension = os.path.basename(path_json)
    file_name, _ = os.path.splitext(json_file_name_with_extension)
    
    # Check if file already exists.
    path_csv = os.path.join(dir_out, '{:}.csv'.format(file_name))
    if os.path.exists(path_csv) and not overwrite:

        print("Output file {:} already exists, skipping conversion.".format(path_csv))
        return

    # Load JSON file.
    with open(path_json, 'r') as file:
        data = json.load(file)

    # Add FIPS code.
    adm_level = file_name.split('__')[-1]
    if adm_level in ['county', 'place']:
        FIPS_code_sublen_dict = {'county' : 3, 'place' : 5}
        FIPS_code_sublen = FIPS_code_sublen_dict[adm_level]
        FIPS_fmt = '{{:02d}}{{:0{:}d}}'.format(FIPS_code_sublen)
        id_name = 'FIPS'
    elif adm_level == 'tract':
        GEOID_fmt = '{:02d}{:03d}{:06d}'
        id_name = 'GEOID'
    elif adm_level == 'block_group':
        GEOID_fmt = '{:02d}{:03d}{:06d}{:01d}'
        id_name = 'GEOID'
    else:
        raise ValueError('Admin level "{:}" not implemented or wrong'.format(adm_level))

    new_data = []
    first_row = True
    for row in data:
        
        print(row)
        new_row = row
        if first_row:
            
            new_row.append(id_name)
            first_row = False

        else:

            if adm_level in ['county', 'place']:

                state_FIPS = int(row[-2])
                county_or_place_FIPS = int(row[-1])
                FIPS = FIPS_fmt.format(state_FIPS, county_or_place_FIPS)
                id_ = FIPS

            elif adm_level == 'tract':

                state_FIPS = int(row[-3])
                county_FIPS = int(row[-2])
                tract_code = int(row[-1])
                GEOID = GEOID_fmt.format(state_FIPS, county_FIPS, tract_code)
                id_ = GEOID

            elif adm_level == 'block_group':

                state_FIPS = int(row[-4])
                county_FIPS = int(row[-3])
                tract_code = int(row[-2])
                block_code = int(row[-1])
                GEOID = GEOID_fmt.format(state_FIPS, county_FIPS, tract_code, block_code)
                id_ = GEOID

            new_row.append(id_)
            
        new_data.append(new_row)
    data = new_data

    # Replace census keys with human readable ones.
    key_header_dict = {}
    for key, header in zip(variable_keys, variable_headers):
        key_header_dict[key] = header
    
    human_readable_header_line = []
    for i, data_key in enumerate(data[0]):
        try:
            #data[0][i] = key_header_dict[data[0][i]]
            human_readable_header_line.append(key_header_dict[data[0][i]])
        except KeyError:
            human_readable_header_line.append(data[0][i])

    # Insert just after first line.
    data.insert(1, human_readable_header_line)

    # Re-order the columns.
    data_new = []
    for row in data:
        row_new = row[-4:] + row[:-4]
        data_new.append(row_new)
    data = data_new

    # Write the transposed data to a CSV file.
    print("Writing to {:}".format(path_csv))
    with open(path_csv, mode='w', newline='') as file:

        writer = csv.writer(file)
        writer.writerows(data)
    
    return

def main():

    # Check that the output directory exists.
    if not os.path.isdir(dir_output):
        raise FileNotFoundError("You must create a directory called 'output'")

    # Set to 'True' to overwrite output files.
    overwrite = False

    # Get data from US census API.
    api_key = load_api_key_from_txt_file()
    paths_json = request_data(api_key, overwrite = overwrite)

    # Convert JSON output into CSV files.
    variable_keys, variable_headers = define_headers()
    for path_json in paths_json:

        convert_json_to_csv(path_json, variable_keys, variable_headers,
                overwrite = overwrite)

    return

if __name__ == '__main__':

    main()
