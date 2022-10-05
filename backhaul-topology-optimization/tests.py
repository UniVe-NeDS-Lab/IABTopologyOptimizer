from pyomo.opt import SolverStatus, TerminationCondition
from collections import Counter
from manage_graphs import compute_tree_size, extract_trees, build_graph, build_multitree_graph
import networkx as nx

donors = set()

ROUNDING_ERROR = 0.0005 # linearization includes some error

class WrongSolution(Exception):
    def __init__(self):
        super().__init__("The solution did not pass the tests:"
                         " Check the logs.")
    pass


def check_solution(model, results, g,  max_out_deg=0):
    error = False
    global donors
    donors = set()
    print('===========')
    print('Starting Tests')
    print('===========')
    gap = 0
    graph = build_graph(g, model, model.u, model.p)

    if (results.solver.status == SolverStatus.ok) and \
       (results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimal Solution Found")
    elif (results.solver.status == SolverStatus.aborted):
        lb = results['Problem'][0]['lower bound']
        ub = results['Problem'][0]['upper bound']
        gap = (ub - lb)/ub
        print(ub,lb,gap)
        error = "Aborted"
    elif (results.solver.termination_condition == TerminationCondition.infeasible):
        print("ERROR: No feasible solution found!")
        error="Infeasible"
    else:
        # Something else is wrong
        print(f"ERROR: Solver Status: {results.solver.status}")
        error=True
    l2_err, max_diam = check_l2_constraints(model)
    flow_err = check_flow_constraints(model, results)
    if max_out_deg:
        tree_err = check_tree_size(model, graph, max_out_deg)
    else:
        tree_err = False
    error = error or l2_err or flow_err or tree_err
    
    #### TODO: test the corner case max_degree=0 and max_diam=0
    #model.f.pprint()
    if error:
        print('=======================')
        print('ERRORS are present')
        print('=======================')
    else:
        print('=======================')
        print('All tests passed')
        print('=======================')

    return len(donors), max_diam, error, gap, graph
    
def check_solution_multitree(model, results, g,  max_out_deg=0):
    error = False
    global donors
    donors = set()
    print('===========')
    print('Starting Tests')
    print('===========')
    gap = 0
    
    graph = build_graph(g, model, model.u, model.p)
    graph_b = build_graph(g, model, model.ub, model.pb)
    multi_graph = build_multitree_graph(g, model)
    if (results.solver.status == SolverStatus.ok) and \
       (results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimal Solution Found")
    elif (results.solver.status == SolverStatus.aborted):
        lb = results['Problem'][0]['lower bound']
        ub = results['Problem'][0]['upper bound']
        gap = (ub - lb)/ub
        print(ub,lb,gap)
        error = "Aborted"
    elif (results.solver.termination_condition == TerminationCondition.infeasible):
        print("ERROR: No feasible solution found!")
        error="Infeasible"
    else:
        # Something else is wrong
        print(f"ERROR: Solver Status: {results.solver.status}")
        error=True
        
    print("== Checking conditions on the main tree == ")
    l2_err, max_diam = check_l2_constraints(model, model.u, model.p)
    main_donors = set([d for d in donors])
    donors = set()
    if max_out_deg:
        tree_err = check_tree_size(model, graph, max_out_deg)
    else:
        tree_err = False
    print("== Checking conditions on the backup tree == ")
    l2_err_b, max_diam_b = check_l2_constraints(model, model.ub, model.pb)
    backup_donors = set([d for d in donors])
    donors = main_donors.union(backup_donors) # resetting the global value
    #flow_err = check_flow_constraints(model, results)
    if max_out_deg:
        tree_err_b = check_tree_size(model, graph_b, max_out_deg)
    else:
        tree_err_b = False

    multi_tree_error = False
    if main_donors & backup_donors:
        print(f"ERROR: nodes {main_donors & backup_donors} are both in the ",
               "main and backup tree")
        multi_tree_error = True
    else:
        print('Trees are separated and contain all nodes')
    
    nodes = set([n for n in model.V if  n not in donors])
    main_nodes = set([n for n in graph.nodes() if n not in donors])
    backup_nodes = set([n for n in graph_b.nodes() if n not in donors])
    if not (main_nodes == backup_nodes == nodes):
        print(f'ERROR: main graph has {len(main_nodes)} and backup graph has'
              ' {len(backup_nodes)} gNBs')
        print(f'       Overall there are {len(nodes)} gNB and {len(donors)} donors')
        multi_tree_error = True
    
    error = error or l2_err or l2_err_b or tree_err or tree_err_b\
            or multi_tree_error
    
    #### TODO: test the corner case max_degree=0 and max_diam=0
    #model.f.pprint()
    if error:
        print('=======================')
        print('ERRORS are present')
        print('=======================')
    else:
        print('=======================')
        print('All tests passed')
        print('=======================')

    return len(donors), max_diam, error, gap, multi_graph

def check_l2_constraints(model, model_u=None, model_p=None):
    distance = Counter()
    diam = max(model.D)
    if not model_u:
        model_u = model.u
    if not model_p:
        model_p = model.p

    # check that diameter is respected
    max_diam = 0
    error = False
    for u in model_u:
        if model_u[u].value > ROUNDING_ERROR:
            if u[1] == 0:
                donors.add(u[0])
            if u[1] > max_diam:
                max_diam = u[1]
                if u[1] > diam:
                    print(f"ERROR: diameter of node {u[0]} is: {u[1]}> {diam}")
                    error = True
            distance[u[0]] += 1
            if distance[u[0]] > 1:
                print(f"ERROR: node {u[0]} has more than one distance variable")
                error = True
    inc_edges = Counter()
    out_edges = Counter()
    if not donors:
        print('ERROR: No Donors in the network!')
        error = True
    # check that incoming degree is respected
    for (i,j) in model_p:
        if model_p[(i,j)].value > ROUNDING_ERROR: # some times solver gives a float 
                                       # solution very close to zero
            inc_edges[j] += 1
            out_edges[i] += 1
            if inc_edges[j] > 1:
                error = True
                print(f'ERROR: node {j} has {inc_edges[j]} incoming edges!')        
    
    # check only valid edges exist
    for (i,j) in model_p:
        if model_p[(i,j)].value > ROUNDING_ERROR and not model.E[(i,j)]:
            print(f"ERROR: edge {(i,j)} was not present in the original graph")
            error=True
    # flow tests
    if not error:
        print(f'Diameter {diam} and single distance is respected')
        print('Incoming edges are respected')
        print('Only original edges are in the graph')
        print('At least one donor exists')

    return error, max_diam

def check_flow_constraints(model, results):
    error = False
    if model.find_component('f'):
        out_flow = {}
        in_flow = {}
        for i in model.V:
            out_flow[i] = 0  # donor nodes
            in_flow[i] = 0
        for i in model.V:
            for j in model.V:
                for h in model.V:
                    out_flow[i] += model.f[(i,j,h)].value                 
                    in_flow[j] += model.f[(i,j,h)].value                 
                    if model.p[(i,j)].value < ROUNDING_ERROR and model.f[(i,j,h)].value > ROUNDING_ERROR:
                        print(f"ERROR: edge {(i,j)} is off and flow {(i,j,h)} is on")
                        error=True    
        total_demand = sum([d for (n,d) in model.demand.items() if n not in out_flow])
        tot_generated_flow = 0
        for i in out_flow:  
            if out_flow[i] > model.capacity[i] + ROUNDING_ERROR:
                print(f'ERROR: node {i} has more output flow than its capacity {model.capacity[i]}')
                error=True
            if i in donors:
                tot_generated_flow += out_flow[i]
        if tot_generated_flow + ROUNDING_ERROR*len(donors)< total_demand:
            print(f'ERROR: total output from root nodes is  {tot_generated_flow} '
                  f'which is lower than the total demand {total_demand}')
            error=True
        for i in in_flow:
            if i in donors and in_flow[i] > ROUNDING_ERROR:
                print(f'ERROR: donor {i} has input flow {in_flow[i]}')
                error=True
            if i not in donors and in_flow[i] + ROUNDING_ERROR < model.demand[i]:
                import pdb
                pdb.set_trace()
                print(f'ERROR: node {i} has flow {in_flow[i]}, less than demand {model.demand[i]}')
                error=True
    if not error:
        print('Flow constraints are respected')
    return error
   
def check_tree_size(model, graph, max_out_deg):
    error = False
    tree_size = compute_tree_size(max(model.D.data()), max_out_deg)[max(model.D.data()), abs(max_out_deg)]
    filtered_g = extract_trees(graph)
    for c in nx.weakly_connected_components(filtered_g):
        if len(c) > tree_size:
            error = True
            print(f'ERROR: tree size is {len(c)} while it should be {tree_size}')
    if not error:
        print(f'Max tree size {tree_size} is respected')
    return error
        
    
    