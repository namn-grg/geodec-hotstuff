from glob import glob
from os.path import join
from re import findall, split

import math
import pandas as pd

from benchmark.utils import PathMaker

#########################################################################################
#########################################################################################
#### GeoDec emulator to study impacts of geospatial diversity on blockchain networks ####
############# Created by Shashank Motepalli, Arno Jacobsen ##############################
#########################################################################################
#########################################################################################
class GeoLogParser:
    @staticmethod
    def count_votes_props(run_id):
        directory = PathMaker.logs_path()
        addresses = []
        proposals = []
        node_num = []
        total_block_commits = 0
        for filename in sorted(glob(join(directory, 'node-*.log'))):
            node_num.append(int(filename.split('-')[1].split('.')[0]))
            with open(filename, 'r') as f:
                data = f.read()
                addr_line = findall(r'Node .* successfully booted', data)
                addr = split(' ', addr_line[0])[1]
                addresses.append(addr)
                prop = findall(r'\[(.*Z) .* Created B\d+ -> ([^ ]+=)', data)
                proposals.append(len(prop))
                commits = findall(r'QC for block: Round:\d.*', data)
                total_block_commits = max(total_block_commits, len(commits))
                    
        votes = [0] * len(addresses)
        
        for filename in sorted(glob(join(directory, 'node-*.log'))):
            votes_temp = [0] * len(addresses)
            with open(filename, 'r') as f:
                logs = f.read()
                qc_lines = findall(r'QC for block: Round:\d.*', logs)
                for n in range(len(qc_lines)):
                    line = qc_lines[n]
                    for i in range(len(addresses)):
                        if addresses[i] in line:
                            votes_temp[i] = votes_temp[i] + 1
                            votes[i] = max(votes[i], votes_temp[i])
    
        votes_data = pd.DataFrame(
            {'address': addresses,
            'votes': votes,
            'proposals': proposals,
            'node_num' : node_num,
            'run_id' : ([run_id] * len(addresses))
            })
        return GeoLogParser._calculate_liveliness(votes_data, total_block_commits)
    
    @staticmethod
    def _calculate_liveliness(data, total_block_commits):
        committe_size = len(data)
        total_committed  = (data['votes'].sum()/ math.ceil((2/3)*committe_size))
        
        total_blocks = max(total_committed, total_block_commits)
        
        data['liveliness'] = (data['votes']/total_blocks) * 100
        
        total_props = data['proposals'].sum()
        data['liveliness_woprops'] = ((data['votes']+data['proposals'])/total_props) * 100
        return data
    
    @staticmethod
    def get_new_run_id():
        data = pd.read_csv('/home/ubuntu/results/geo-dec-metrics.csv')
        return (data['run_id'].max() + 1)
    
    @staticmethod
    def aggregate_runs(run_id_array):
        data = pd.read_csv('/home/ubuntu/results/geo-dec-metrics.csv')
        
        data = data.loc[data['run_id'].isin(run_id_array)]
        by_name = data.groupby(['name'])

        # for name, liveliness in by_name:
        #     print(f"entries for {name!r}")
        #     print("------------------------")
        #     print(liveliness.head(3), end="\n\n")

        liveliness_mean = by_name['liveliness'].mean(numeric_only= True).reset_index()
        liveliness_mean.rename(columns = {'liveliness':'liveliness_avg'}, inplace = True)

        data_first = data.loc[data['run_id'] == run_id_array[0]]
        result = pd.merge(data_first, liveliness_mean, on='name')
        result['runs'] = ([len(run_id_array)] * len(result))
        return result