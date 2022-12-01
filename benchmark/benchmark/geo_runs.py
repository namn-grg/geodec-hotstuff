#!/usr/bin/python3

import datetime
import os
import pandas as pd
import random
from re import sub
import subprocess
import sys
import math

from time import sleep
from geodec import GeoDec

SERVERS_FILE  = '/home/ubuntu/data/servers-2020-07-19.csv'
MARKED_SERVERS_FILE = '/home/ubuntu/data/servers-2020-07-19-us-europe-filter-2.csv'
COMMITTEE_SIZE = 64 #16

def change_config(config, rate, batch_size, message_size):
    with open(config, 'r') as f:
        lines = f.readlines()

    flag = False

    for i in range(len(lines)):
        if lines[i].startswith("def remote(ctx):"):
            flag = True
        if flag:
            print(lines[i])
            if lines[i].startswith("        'rate':"):
                lines[i] = f"        'rate': [{rate}],\n"
            elif lines[i].startswith("        'tx_size': "):
                lines[i] = f"        'tx_size': {message_size},\n"
            elif "'batch_size':" in lines[i]:
                lines[i] = f"            'batch_size': {batch_size * message_size},\n"
    with open(config, 'w') as f:
        f.writelines(lines)

def change_location_input(config, geo_input):
    with open(config, 'r') as f:
        lines = f.readlines()
        flag = False
        for i in range(len(lines)):
            if lines[i].startswith("def remote(ctx):"):
                flag = True
            if flag:
                if lines[i].startswith("    geoInput"):
                    lines[i] = f"    geoInput = {geo_input}\n"
    
    with open(config, 'w') as f:
        f.writelines(lines)

def get_server_locations(self):
    servers_locs = pd.read_csv(SERVERS_FILE)['id'].values.tolist()
    return servers_locs

def get_random_input(locations):
    geo_input = {}
    for i in range(COMMITTEE_SIZE):
        random_loc = random.choice(locations)
        if random_loc in geo_input.keys():
            geo_input[random_loc] = 1 + geo_input[random_loc]
        else:
            geo_input[random_loc] = 1
    return geo_input

def get_custom_input(majority, minority, majority_count):
    geo_input = {}
    geo_input[majority] = majority_count
    minority_size = COMMITTEE_SIZE - majority_count
    if(minority_size > 0):
        geo_input[minority] = minority_size
    return geo_input

def get_custom_input_twomajorities(majority, minority, i):
    geo_input = {}
    geo_input[minority] = i
    majority_size = math.floor((COMMITTEE_SIZE - i)/2)
    majority1_size = COMMITTEE_SIZE - i - majority_size
    geo_input[majority[0]] = majority_size
    geo_input[majority[1]] = majority1_size
    return geo_input

def get_continent_data(continent_codes):
    servers = pd.read_csv(SERVERS_FILE)
    continent_servers = servers[servers["continent"].isin(continent_codes)]
    servers_locs = continent_servers['id'].values.tolist()
    return servers_locs

def get_us_europe_validators(signal):
    servers = pd.read_csv(MARKED_SERVERS_FILE)
    selected_servers = servers[servers["is_US_Europe"]==signal]
    return selected_servers['id'].values.tolist()
    
def get_us_europe_rest_distribution(minority_size):
    geo_input = {}
    us_europe_ids = get_us_europe_validators(1)
    minority_ids = get_us_europe_validators(0)

    # randomly get minorities, it is in multiples of 2
    x = minority_size
    while x > 0:
        random_loc = random.choice(minority_ids)
        if random_loc in geo_input.keys():
            geo_input[random_loc] = 4 + geo_input[random_loc]
        else:
            geo_input[random_loc] = 4
        x = x - 4
    
    # fill in the remaining seats with majority, each location has six
    majority_size = COMMITTEE_SIZE - minority_size
    while majority_size > 0:
        number = majority_size
        if majority_size > 8 :
            number = 8
            majority_size = majority_size - number
        else: 
            majority_size = 0
        random_loc = random.choice(us_europe_ids)
        
        if random_loc in geo_input.keys():
            geo_input[random_loc] = number + geo_input[random_loc]
        else:
            geo_input[random_loc] = number
    
    return geo_input

## this function checks if we have all the pairs of data for exsiting inputs
def check_if_valid_input(geo_input, pingDelays):
    keys = list(geo_input.keys())
    
    for source in keys:
        for destination in keys:
            if source != destination:
                query = 'source == ' + str(source) + ' and destination == '+ str(destination)
                delay_data = pingDelays.query(query) 
                if(delay_data is None):
                    return False            
    return True

if __name__ == "__main__":


    locations = get_server_locations(SERVERS_FILE)
    #################################
    ##### RANDOM INPUT RUNS #########
    #################################
    # i = 300
    # while(i>0):
    #     i = i -1
    #     # Get random inputs from the runs
    #     geo_input = get_random_input(locations)
    #     change_location_input("fabfile.py", geo_input)
        
    #     now = datetime.datetime.now()
    #     print("==============================================================")
    #     print(str(now) + " Running "+ str(i) +" test with " + str(geo_input))

    #     subprocess.run(["fab", "remote"])

    #     print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #     sleep(1)
    ##################################################################
    ### Show the minority rise with change ###########################
    ##################################################################
    # minority_nodes = [222, 52, 53, 4, 210, 72, 6]
    # majority_nodes = [45]
    # for majority in majority_nodes:
    #     for minority in minority_nodes:
    #         i = COMMITTEE_SIZE
    #         while(i>(COMMITTEE_SIZE/2)):
    #             geo_input = get_custom_input(majority, minority, i)
    #             change_location_input("fabfile.py", geo_input)
                
    #             now = datetime.datetime.now()
    #             print("==============================================================")
    #             print(str(now) + " Running "+ str(i) +" test with " + str(geo_input))

    #             subprocess.run(["fab", "remote"])

    #             print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #             sleep(1)
    #             i = i -1
    
    #######################################################    
    # # MINORITY IN ONE CONTINENT #########################
    #######################################################
    ## Majority in Helinski, Finland and Santa Clara, US
    # majority = [45, 23]
    # rest_servers = [31, 1]
    # for minority in rest_servers:
    #     i = 1
    #     while i < 3=:
    #         geo_input = get_custom_input_twomajorities(majority, minority, i)
    #         change_location_input("fabfile.py", geo_input)
                
    #         now = datetime.datetime.now()
    #         print("==============================================================")
    #         print(str(now) + " Running "+ str(i) +" test with " + str(geo_input))

    #         subprocess.run(["fab", "remote"])

    #         print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #         sleep(1)
    #         i = i +1
    
    ##################################################################
    ### 64 nodes. Majority in US/Europe. Keep varying the minority####
    ### We pick all nodes from these locations randomly ##############
    ##################################################################
    geodec = GeoDec()
    
    runs  = 1
    
    while runs > 0:
        runs = runs - 1
        
        minority_count = 24
        
        while minority_count > 0:
            
            geo_input = get_us_europe_rest_distribution(minority_count)
            pingDelays = geodec.getPingDelay(geo_input, "/home/ubuntu/data/pings-2020-07-19-2020-07-20-grouped.csv", "/home/ubuntu/data/pings-2020-07-19-2020-07-20.csv")    
            
            # change_location_input("fabfile.py", geo_input)
            if(check_if_valid_input(geo_input, pingDelays)):
                now = datetime.datetime.now()
                print("==============================================================")
                print(str(now) + " Running "+ str(runs) +" test with " + str(geo_input) + " minority count is "+ str(minority_count))

                subprocess.run(["fab", "remote"])

                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                sleep(1)
 
                minority_count = minority_count - 4
    
    #######################################################    
    #### BASIC RUNS #######################################
    #######################################################    
    
    # message_sizes = [ 16, 32]
    # batch_sizes = [200, 500, 1000, 10000, 20000, 50000, 80000, 100000]
    # tgt_tp = [20000 , 30000, 50000, 100000, 200000, 450000]
    # repeat = 5

    # print("Starting benchmarking tool")
    # for t in tgt_tp:
    #     for m in message_sizes:
    #         for b in batch_sizes:
    #             for i in range(repeat):
    #                 run = f"run_m{m}_b{b*m}_t{t}_repeat{i}"
    #                 now = datetime.datetime.now()

    #                 print("==============================================================")
    #                 print(str(now) + " Running test: " + run)

    #                 change_config("../fabfile.py", t, b, m)
    #                 subprocess.run(["fab", "remote"])

    #                 print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #                 sleep(1)

    print("Benchmarking finished")