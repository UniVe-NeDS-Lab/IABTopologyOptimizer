#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
from pathlib import Path
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import math
from collections import defaultdict
from manage_graphs import compute_tree_size
import matplotlib
matplotlib.use("TkAgg")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', default='results/')
    parser.add_argument('--model', help='limit the analysis to l2/flow', 
                        default='')
    parser.add_argument('--type', help='limit the analysis to erdosh/poisson', 
                        default='')
    parser.add_argument('--metric', help='which metric to plot', 
                        choices=['time', 'distance', 'degree', 'out_degree', 
                                 'l2', 'tree_size', 'flow_allocation'])
    args = parser.parse_args()
    return args

def strtosec(t):
    return float(''.join(x for x in t if x.isnumeric()))    


def load_results_files(folder, model, g_type):
    data = []
    index_names = []
    indices = []
    degree_data = []
    index_names = ["n", "r", "type", "model", "diam", "deg", "capacity", 
                   "seed", "timelimit", "run_id"]
    column_names = ["donors", "diameter", "time", "error_status", "gap"]
    

    column_names += ['out_degree', 'avg_distance_to_donor',
                     'avg_tree_size']
    
    position_data = []
    
    #data = pandas.DataFrame(columns=column_names, index=index_names)
    for path in Path(folder).rglob('results.json'):
        with open(path.resolve()) as f:
            r = json.load(f)
            if (model and r['config']['model'] != model) or \
                    (g_type and r['config']['type'] != g_type):
                continue
      
            folder_path = Path(path).parents[0]
            for run in r['runs']:
                # unofortunately in the first batch of results there were
                # different keys so this code must integrate the results 
                # if not present.
                data_dict = {k:0 for k in index_names+column_names}
                for col in data_dict:
                    try:
                        data_dict[col] = r['config'][col]
                    except KeyError:
                        pass
                
                #data_dict = {k:0 for k in column_names}
                run_id = run['run_id']
                data_dict['run_id'] = run_id
                #indices.append(index_dict.values())
                #print(max_diam, max_out_deg, tree_size)

                graph_file_name = folder_path / str(run_id) / 'graph.graphml'            
                g = nx.read_graphml(graph_file_name)
                data_dict['out_degree'] = sum([x[1] for x in g.out_degree(g.nodes)])/len(g)

                        
                g.remove_edges_from([(s,d) for (s,d) in g.edges() if g[s][d]['label'] == 'off'])
                donors = [n for n,d in g.nodes(data=True) if d['label'] == 'donor'] 
                shortest_path_lengths = {n:100 for n in g if n not in donors}
                tree_size = {}
                tree_demand = {}
                if r['config']['model'] in ['l2']:
                    max_tree_size = max(compute_tree_size(r['config']['diam'], r['config']['deg']).values())
                for d in donors:
                    spl = nx.single_source_shortest_path_length(g, d)      
                    tree_nodes = 0
                    subtree_demand = 0
                    tree_nodes = len(spl)
                    for n in shortest_path_lengths:
                        try:
                            shortest_path_lengths[n] = min(shortest_path_lengths[n], spl[n])
                            subtree_demand += g.nodes[n]['weight']
                        except KeyError:
                            pass
                    tree_size[d] = tree_nodes
                    tree_demand[d] = subtree_demand
                for n in g:
                    measure = {}
                    measure['node'] = n
                    measure['n'] = r['config']['n']
                    measure['degree'] = g.out_degree(n)
                    measure['type'] = r['config']['type']
                    if n in donors:
                        measure['tree_size'] = tree_size[n]
                        if r['config']['model'] in ['l2']:
                            measure['max_tree_size'] = max_tree_size
                            measure['best_tree_size'] = r['config']['n']/math.ceil(r['config']['n']/measure['max_tree_size'])
                        elif r['config']['model'] in ['flow']:
                            measure['max_capacity'] = r['config']['capacity']
                            measure['allocated_capacity'] = tree_demand[n]
                    degree_data.append(measure)
                    try:
                        geo = {}
                        n_d = g.nodes[n]
                        geo['x'] = n_d['x']
                        geo['y'] = n_d['y']
                        geo['type'] = r['config']['type']
                        geo['donor'] = n_d['label'] == 'gNb'
                        position_data.append(geo)
                    except KeyError:    
                        pass
                #data_dict['avg_tree_size'] = tree_size#sum(tree_size)/len(tree_size)
                data_dict['avg_distance_to_donor'] = sum(shortest_path_lengths.values())/len(shortest_path_lengths)
                for column in column_names:
                # the dictionary is needed to keep the same ordering
                    try:
                        if column == 'time':
                            data_dict[column] = strtosec(run[column])
                        else:
                            data_dict[column] = run[column]
                    except KeyError:
                        pass          
                data.append(list(data_dict.values()))

    #index = pd.MultiIndex.from_tuples(indices, names=index_names)
    d = pd.DataFrame(data, columns=index_names+column_names)
    #d = pd.DataFrame(data, columns=column_names)
    degree_df = pd.DataFrame(degree_data)
    if position_data:
        position_df = pd.DataFrame(position_data)
    else:
        position_df = None
    return d, degree_df, position_df 


def plot_degree(d):
    # Apply the default theme
    sns.set_theme()

    fg = sns.FacetGrid(data=d, col='n', hue='type', col_wrap=4)
    fg.map_dataframe(sns.histplot, cumulative=False, x='degree', stat='density', 
                     discrete=True, common_bins=True)
    plt.show()

def plot_out_degree(d):
    # Apply the default theme
    sns.set_theme()

    # Create a visualization
    sns.relplot(
        data=d,
        x="n", y="out_degree", col="type",err_style="band",
        #ci=None, estimator=np.median,
        kind='line')
    plt.show()

def plot_time(d):
    # Apply the default theme
    sns.set_theme()

    # Create a visualization
    mask = d['n']<60
    fg = sns.FacetGrid(data=d.loc[mask], col='model')
    #sns.factorplot("a", hue="b", y="c", data=df_long, kind="box")
    m = fg.map_dataframe(sns.boxplot, x='n', y='time', hue='type', orient='v')
    m.set(yscale="log")
    plt.show()

def plot_flow_allocation(d):
    # Apply the default theme
    sns.set_theme()

    # Create a visualization
    
    fg = sns.FacetGrid(data=d, col='type')
    #sns.factorplot("a", hue="b", y="c", data=df_long, kind="box")
    m = fg.map_dataframe(sns.boxplot, x='n', y='allocated_capacity', orient='v')
    #fg2 = sns.FacetGrid(data=d,col='max_capacity')
    #m2 = fg2.map_dataframe(sns.lineplot, x='n', y='best_tree_size')
    print(d.loc[d['allocated_capacity']>0])
    #sns.boxplot(data=d, x='size', y='tree_size', orient='v')
    #m.set(yscale="log")
    plt.show()

def plot_tree_size(d):
    # Apply the default theme
    sns.set_theme()

    # Create a visualization
    
    fg = sns.FacetGrid(data=d, col='max_tree_size')
    #sns.factorplot("a", hue="b", y="c", data=df_long, kind="box")
    m = fg.map_dataframe(sns.boxplot, x='n', y='tree_size', orient='v')
    fg2 = sns.FacetGrid(data=d,col='max_tree_size')
    m2 = fg2.map_dataframe(sns.lineplot, x='n', y='best_tree_size')
    print(d)
    #sns.boxplot(data=d, x='size', y='tree_size', orient='v')
    #m.set(yscale="log")
    plt.show()

def plot_distance(d):
    # Apply the default theme
    sns.set_theme()
    # Create a visualization
    fg = sns.FacetGrid(data=d, col='type')
    #sns.factorplot("a", hue="b", y="c", data=df_long, kind="box")
    m = fg.map_dataframe(sns.displot, x='x', y='y')
    sns.displot(data=d, x='x', y='y', col='type')
    #sns.kdeplot(data=d.loc[d['type']=='poisson_weighted'], x='x', y='y', fill='true')
    #sns.kdeplot(data=d.loc[d['type']=='poisson'], x='x', y='y',  fill='true')

    #m = fg.map_dataframe(sns.boxplot, x='n', y='time', hue='type', orient='v')
    plt.show()

def plot_l2(d):
    # Apply the default theme
    sns.set_theme()

    # Create a visualization
    fg = sns.FacetGrid(data=d, col='diam',row='deg')
    #sns.factorplot("a", hue="b", y="c", data=df_long, kind="box")
    m = fg.map_dataframe(sns.lineplot, x='n', y='donors')
    ax2 = plt.twinx()
    m = fg.map_dataframe(sns.lineplot, x='n', y='avg_distance_to_donor', ax=ax2)
    plt.legend(['donors', 'distance_to_donor'])
    plt.show()

def print_summary(d, deg, pos):
    print('=========== Summary o results ===========')
    print(f"Average number of donors: {d['donors'].mean()}")
    print(f"Average distance to donors: {d['avg_distance_to_donor'].mean()}")
    print(f"Average tree size: {d['avg_tree_size'].mean()}")
    print(d)

if __name__ == '__main__':
    args = parse_arguments()
    d, degree_df, position_df= load_results_files(args.folder, args.model, args.type)
    if args.metric == 'time':
        plot_time(d)
    if args.metric == 'distance':
        plot_distance(position_df)
    if args.metric == 'out_degree':
        plot_out_degree(d)
    if args.metric == 'degree':
        plot_degree(degree_df)
    if args.metric == 'l2':
        plot_l2(d)
    if args.metric == 'tree_size':
        plot_tree_size(degree_df)
    if args.metric == 'flow_allocation':
        plot_flow_allocation(degree_df)
    print_summary(d, degree_df, position_df)
