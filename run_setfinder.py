#!/usr/bin/env python3
"""
Author : Travis Simmons
Date   : July 2nd 2024
Purpose: Process reach data to create set.jsons for FLPE algorithms
"""
# Sample deployment

# standard imports
import argparse
import os
import glob
import json

# 3rd party imports
import netCDF4 as ncf

# local imports
from sets.getAllSets import generate_sets

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i',
                        '--index',
                        help='Index that indicates what continent to run on',
                        metavar='index',
                        type=int)

    parser.add_argument('-a',
                        '--algorithms',
                        help='A list of algorithm names',
                        nargs='+')
    
    parser.add_argument('-e', 
                        '--expanded', 
                        action='store_true', 
                        help='Expanded mode')

    parser.add_argument('-n',
                        '--indir',
                        help='Path to input directory',
                        metavar='indir',
                        type=str)

    parser.add_argument('-o',
                        '--outdir',
                        help='Path to output directory',
                        metavar='outdir',
                        type=str)

    parser.add_argument('-s',
                        '--sword_version',
                        help='Sword version number',
                        metavar='sword_version',
                        type=int)

    return parser.parse_args()


def get_continent(indir:str, index:int):
    # open continent .json to find what continent we are running on
    continent_json_filepath = os.path.join(indir, 'continent.json')

    with open(continent_json_filepath) as jsonfile:
        data = json.load(jsonfile)

    continent_prefix = list(data[index].keys())[0]

    continent_id_list = data[index][continent_prefix]

    return continent_prefix, continent_id_list

def get_reach_list(indir:str, continent_prefix:str, continent_id_list:list, expanded:bool):


    # read in data depending on if it is the first or second run of the setfinder and return a list of reaches to consider

    if expanded:
        with open(os.path.join(indir, 'reaches_of_interest.json')) as jsonfile:
            reaches_of_interest = json.load(jsonfile)
        
        #filter by continent
        reach_list = [i for i in reaches_of_interest if str(i)[0] in continent_id_list]
    else:
        reach_list = [os.path.basename(i).split('_')[0] for i in glob.glob(os.path.join(indir, 'swot', '*.nc'))]

    return reach_list

def save_reach_list(outdir:str, reach_list:list, continent_prefix:str, expanded:bool):
    print('saving reach list')

    if expanded:
        output_filepath = os.path.join(outdir, f'expanded_reaches_of_interest_{continent_prefix}.json')
    else:
        output_filepath = os.path.join(outdir,f'reaches_{continent_prefix}.json')

    with open(output_filepath, 'w') as jsonfile:
        json.dump(reach_list, jsonfile)

def parse_reach_list_for_output(reach_list:list, continent_prefix:str, sword_version:int,outdir:str):

#   {
#     "reach_id": 12798000121,
#     "sword": "af_sword_v16_patch.nc",
#     "swot": "12798000121_SWOT.nc",
#     "sos": "af_sword_v16_SOS_priors.nc"
#   }

    reach_dict_list = []
    for i in reach_list:
        reach_dict_list.append(
            {
            "reach_id": int(i),
            "sword": f"{continent_prefix}_sword_v{sword_version}.nc",
            "swot": f"{i}_SWOT.nc",
            "sos": f"{continent_prefix}_sword_v{sword_version}_SOS_priors.nc"
            }
        )
    return reach_dict_list
    
def main():

    # Arguments
    args = get_args()

    index = args.index
    algorithms = args.algorithms
    indir = args.indir
    outdir = args.outdir
    sword_version = args.sword_version
    expanded = args.expanded

    # Get index, index -235 indicates that we are running in aws in the management account
    if index == -235:
        index=int(os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX"))
    elif index == -999:
        # will become the ops environment variable
        index = index
  
    # Find continent prefix for filtering reaches
    continent_prefix, continent_id_list = get_continent(indir=indir, index=index)

    # SWORD
    sword_filepath = os.path.join(indir, 'sword', f'{continent_prefix}_sword_v{sword_version}.nc')
    sword = ncf.Dataset(sword_filepath)

    # Get list of reaches to make sets out of, if expanded look for /mnt/input/swot, if not look for reaches_of_interest.json
    reach_list = get_reach_list(indir=indir, continent_prefix=continent_prefix, continent_id_list=continent_id_list, expanded=expanded)
    save_reach_list(outdir=outdir, reach_list=reach_list, continent_prefix=continent_prefix, expanded=expanded)

    reach_dict_list = parse_reach_list_for_output(reach_list=reach_list, continent_prefix=continent_prefix, sword_version=sword_version, outdir=outdir)

    # Generate sets for FLPEs
    generate_sets(reaches = reach_dict_list, continent=continent_prefix, 
                    output_dir = outdir, algorithms = algorithms, 
                        sword_dataset = sword, sword_filepath = sword_filepath, 
                        expanded = expanded)

# --------------------------------------------------
if __name__ == '__main__':
    main()