import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import lognorm
from numpy import exp, log, pi
from numpy.random import uniform
from numpy.random import seed as np_seed
import random 
import datetime

def make_line(n):
    g = nx.path_graph(n).to_directed()
    return g

def set_seed(seed):
    if not seed:
        seed = int(datetime.datetime.now().timestamp())
    random.seed(seed)
    np_seed(seed)
    print(f'using seed {seed}')
    return seed
        
def make_random_graph(n, prob=0, seed=0):
    seed = set_seed(seed)
    if not prob:
        prob = log(n)/n
    for i in range(100):
        g = nx.erdos_renyi_graph(n, prob).to_directed()
        if nx.is_strongly_connected(g):
            break
    else:
        print("Disconnected graph, increase the edge probability")
        exit()
    print(f'Created a graph with {len(g)} nodes and {len(g.edges())} directed archs')
    return g, seed

def make_poisson_graph(n, density=50, seed=0, border=100):
    # density = nodes per squared km
    area = n/density
    size = int(area**0.5*1000) + border*2
    coords = {}
    sigma=0.9
    mu=3.04,
    seed = set_seed(seed)
    F = lognorm(s=sigma, scale=exp(mu)).cdf
    def plos(F, d, h=9, l=1/1430, r=8.07):
       return exp(-l*(1-F(h))*(2*r*d-pi*r**2))
   
    found = False
    while not found:
        for i in range(100):
            g = nx.DiGraph()
            for i in range(1,n+1):
                coords[i] = [uniform(border,size-border),
                             uniform(border,size-border)]
                g.add_node(i, x=coords[i][0], y=coords[i][1])
            for i in range(1,n+1):
                for j in range(i+1,n+1):
                    d = ((coords[i][0]-coords[j][0])**2 + 
                         (coords[i][1]-coords[j][1])**2)**0.5
                    if uniform() < plos(F,d):
                        g.add_edge(i,j)
                        g.add_edge(j,i)
            if nx.is_strongly_connected(g):
                found = True
                break
        else:
            density = density*1.1
            area = n/density
            size = int(area**0.5*1000) + border*2
            print(f"Can not find a connected graph, increasing the density to {density} ")
            
    print(f'Created a graph with {len(g)} nodes and {len(g.edges())}'
          f' directed archs on a {size}x{size}m area, with density {density}')
    return g, coords, seed

def compute_tree_size(max_diam, max_out_deg, decr=0):
    tree_size = {}
    if max_out_deg < 0:
        max_out_deg = -max_out_deg
        decr = 1
    for j in range(2, max_out_deg+1):
        for i in range(1, max_diam+1):
            nodes = 1
            level_nodes = 1
            degree = j
            for r in range(1, i+1):
                if not degree:
                    break
                level_nodes = level_nodes*degree
                degree -= decr
                nodes += level_nodes
            tree_size[(i,j)] = nodes
    return tree_size


def build_graph(g, model, model_u, model_p):
    donors_count = 0
    newg = nx.DiGraph()
    newg.add_nodes_from(g.nodes(data=True))
    for u in model_u:
        if model_u[u].value >= 0.5:
            if u[1] == 0:
                # then donor
                newg.nodes[u[0]]['label'] ='donor'
                donors_count += 1
            else:
                newg.nodes[u[0]]['label'] ='gNB'
    for e in model_p:
            if model_p[e].value > 0.5:
                f = 0
                if model.find_component('f'):
                    f = sum([model.f[e[0], e[1], h].value for h in model.V]) 
                newg.add_edge(e[0], e[1], label=f'{f}')
            elif e in g.edges():
                newg.add_edge(e[0], e[1], label='off')
    newg.nodes()
    return newg

    
def build_multitree_graph(g, model):
    newg = nx.MultiDiGraph()
    newg.add_nodes_from(g.nodes(data=True))
    for u in model.u:
        if model.u[u].value >= 0.5:
            if u[1] == 0:
                # then donor
                newg.nodes[u[0]]['label'] ='donor_main'
        elif model.ub[u].value >= 0.5:
            if u[1] == 0:
                # then donor
                newg.nodes[u[0]]['label'] ='donor_backup'
        if (model.ub[u].value >= 0.5 or model.u[u].value >= 0.5) and u[1] !=0:
                newg.nodes[u[0]]['label'] ='gNB'
            
    for e in model.p:
            if model.p[e].value > 0.5:
                newg.add_edge(e[0], e[1], label='on_main')
            if model.pb[e].value > 0.5:
                newg.add_edge(e[0], e[1], label='on_backup')
            e_rev = (e[1], e[0])
            if model.p[e].value < 0.5 and model.pb[e].value < 0.5 and\
               model.p[e_rev].value < 0.5 and model.pb[e_rev].value < 0.5 and\
                    e in g.edges():
                newg.add_edge(e[0], e[1], label='off')
    return newg
                        
def extract_trees(g):
    
    def is_on(fr, to):
        return g[fr][to]['label'] not in ['off']
    
    return nx.subgraph_view(g, filter_edge=is_on)    



def set_graph_colors(newg, donors_main, gNBs, donors_backup = []):
    pos = {}
    try:
        for n in newg.nodes(data=True):
            pos[n[0]] = (n[1]['x'], n[1]['y'])
    except KeyError:
        try:
            pos = nx.nx_agraph.graphviz_layout(newg)
        except ImportError:
            pos = nx.kamada_kawai_layout(newg)
    try:
        donors_color = []
        backup_donors_color = []
        gnb_color = []
        max_weight = max([w[1]['weight'] for w in newg.nodes(data=True)])
        min_weight = min([w[1]['weight'] for w in newg.nodes(data=True)])

        for n in donors_main:
            donors_color.append(newg.nodes[n]['weight'])
        for n in donors_backup:
            backup_donors_color.append(newg.nodes[n]['weight'])        
        for n in gNBs:
            gnb_color.append(newg.nodes[n]['weight'])

        color_map = matplotlib.cm.ScalarMappable(cmap="Reds", 
                    norm=matplotlib.colors.Normalize(vmin=min_weight, 
                                                     vmax=max_weight,))

    except KeyError:
        gnb_color = '#00ffff'
        donors_color = '#ff0000'
        backup_donors_color = '#ff0000'
        color_map = {}
    return pos, gnb_color, donors_color, color_map, backup_donors_color

def save_multitree_graph(newg, edges_label=True, outfolder='./', labels=True):
    
    nx.write_graphml_xml(newg, outfolder+'graph.graphml')
    f = plt.figure()
    #print(newg.nodes(data=True), newg.edges(data=True))
    donors_main = [n[0] for n in newg.nodes(data=True) if n[1]['label'] == 'donor_main'] 
    donors_backup = [n[0] for n in newg.nodes(data=True) if n[1]['label'] == 'donor_backup'] 
    
    gNBs = [n[0] for n in newg.nodes(data=True) if n[1]['label'] == 'gNB'] 
    edges_on_main = {(e[0], e[1]):e[2]['label'] for e in newg.edges(data=True) if 
                     e[2]['label'] == 'on_main'}
    edges_on_backup = {(e[0], e[1]):e[2]['label'] for e in newg.edges(data=True) if 
                     e[2]['label'] == 'on_backup'}   
    
    edges_off = [(e[0], e[1]) for e in newg.edges(data=True) if e[2]['label'] == 'off'] 
    print('donors:', donors_main, donors_backup)
    print('gNB:', gNBs)
    res = set_graph_colors(newg, donors_main, gNBs, donors_backup)
    pos, gnb_color, main_donors_color, color_map, backup_donors_color = res
    node_size=300

    if labels:
        nx.draw_networkx_labels(newg, pos)
    else:
        node_size=100
        
    nx.draw_networkx_nodes(newg, pos, nodelist=gNBs, node_shape='o',
                           node_color=gnb_color, cmap='Reds', node_size=node_size)
    nx.draw_networkx_nodes(newg, pos, nodelist=donors_main, node_shape='s',
                           node_color=main_donors_color, 
                           cmap='Reds', linewidths=1, edgecolors="Black", node_size=node_size)
    nx.draw_networkx_nodes(newg, pos, nodelist=donors_backup, node_shape='h',
                           node_color=backup_donors_color,
                           cmap='Reds', linewidths=1, edgecolors="Black", node_size=node_size)

    if color_map:
        plt.colorbar(color_map)
  
 
    nx.draw_networkx_edges(newg, pos, edgelist=edges_off, style=':',
                           arrows=False, alpha=0.1) 
    nx.draw_networkx_edges(newg, pos, edgelist=edges_on_main.keys(), 
                           connectionstyle='arc3, rad = 0.1')
    nx.draw_networkx_edges(newg, pos, edgelist=edges_on_backup.keys(), 
                           connectionstyle='arc3, rad = 0.1', edge_color='b')    
    plt.title(f'Nodes: {len(newg)}; Archs (directed):{len(newg.edges())};'
              f' Active Archs: {len(edges_on_main)+len(edges_on_backup)}')
    f.savefig(outfolder+'graph.png', dpi=900)
    plt.close()

def save_graph(newg, edges_label=True, outfolder='./', labels=True):
    
    nx.write_graphml_xml(newg, outfolder+'graph.graphml')
    f = plt.figure()
    donors = [n[0] for n in newg.nodes(data=True) if n[1]['label'] == 'donor'] 
    gNBs = [n[0] for n in newg.nodes(data=True) if n[1]['label'] == 'gNB'] 
    edges_on = {(e[0], e[1]):e[2]['label'] for e in newg.edges(data=True) if 
                e[2]['label'] != 'off'}
    edges_labels = {(e[0], e[1]):e[2]['label'] for e in newg.edges(data=True) if 
                e[2]['label'] not in ['off', '0']}
    edges_off = [(e[0], e[1]) for e in newg.edges(data=True) if e[2]['label'] == 'off'] 
    print('donors:', donors)
    print('gNB:', gNBs)
    pos, gnb_color, donors_color, color_map, _ = set_graph_colors(newg, donors, gNBs)
  
    node_size=300
    if labels:
        nx.draw_networkx_labels(newg, pos)
    else:
        node_size=100
        
    nx.draw_networkx_nodes(newg, pos, nodelist=gNBs, node_shape='o',
                           node_color=gnb_color, cmap='Reds', node_size=node_size)
    nx.draw_networkx_nodes(newg, pos, nodelist=donors, node_shape='s',
                           node_color=donors_color, cmap='Reds', 
                           linewidths=1, edgecolors="Black", node_size=node_size)
    if color_map:
        plt.colorbar(color_map)
    nx.draw_networkx_edges(newg, pos, edgelist=edges_off, style=':',
                           arrows=False, alpha=0.1) 
    nx.draw_networkx_edges(newg, pos, edgelist=edges_on.keys())
    
    if edges_label:
        nx.draw_networkx_edge_labels(newg, pos, edge_labels=edges_labels,
                                     font_size=7)                      
    plt.title(f'Nodes: {len(newg)}; Archs (directed):{len(newg.edges())};'
              f' Active Archs: {len(edges_on)}')
    f.savefig(outfolder+'graph.png', dpi=900)
    plt.close()
    