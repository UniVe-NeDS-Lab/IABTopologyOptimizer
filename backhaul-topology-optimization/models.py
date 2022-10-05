#!/usr/bin/env python3

import pyomo.environ as pyo


def make_l2_multitree_model(model, nodes, edges, max_diam, max_out_deg):
    
    model.D = pyo.RangeSet(0, max_diam)
    model.D_pos = pyo.RangeSet(1, max_diam)
    model.V = pyo.Set(initialize=nodes)

    def edge_init(model, i, j):
        return (i,j) in edges
    
    model.E = pyo.Param(model.V, model.V, initialize=edge_init, 
                        domain=pyo.Binary)
    model.u = pyo.Var(model.V, model.D, domain=pyo.Binary, initialize=0)
    model.p = pyo.Var(model.V, model.V, domain=pyo.Binary, initialize=0)
    model.ub = pyo.Var(model.V, model.D, domain=pyo.Binary, initialize=0)
    model.pb = pyo.Var(model.V, model.V, domain=pyo.Binary, initialize=0) 
    
    def objective(model):
        return sum([model.u[i,0] + model.ub[i,0] for i in model.V])
    
    def dist_c(model,i):
        return sum([model.u[i,l] for l in model.D]) == 1 - model.ub[i,0]

    def dist_cb(model,i):
        return sum([model.ub[i,l] for l in model.D]) == 1 - model.u[i,0]
    
    def double_tree(model,i):
        return sum([model.u[i,l] + model.u2[i,l] for l in model.D_pos]) >= 2
    
    def no_double_root(model,i):
        return model.u[i,0] + model.ub[i,0] <= 1
    
    def one_incoming(model, j):
        return sum([model.p[i,j] for i in model.V]) == 1 - model.u[j,0] - model.ub[j,0]
    
    def one_incomingb(model, j):
        return sum([model.pb[i,j] for i in model.V]) == 1 - model.ub[j,0] - model.u[j,0]
    
    def max_deg(model, i):
        return sum([model.p[i,j] for j in model.V]) <= model.deg
    
    def max_degb(model, i):
        return sum([model.pb[i,j] for j in model.V]) <= model.deg
    
    def max_deg_decr(model, i, j):
        return sum([model.p[i,k] for k in model.V]) <= model.deg - j*model.u[i,j] 
  
    def max_deg_decrb(model, i, j):
        return sum([model.pb[i,k] for k in model.V]) <= model.deg - j*model.ub[i,j] 
 
    def incremental_distance(model, i, j, l):
        return model.p[i,j] <= 1 - model.u[j,l] + model.u[i,l-1]
        
    def incremental_distanceb(model, i, j, l):
        return model.pb[i,j] <= 1 - model.ub[j,l] + model.ub[i,l-1]
    
    def distance_implies_incoming(model, j):
        return sum([model.u[j,l] for l in model.D_pos]) <= sum([model.p[i,j] for i in model.V])

    def distance_implies_incomingb(model, j):
        return sum([model.ub[j,l] for l in model.D_pos]) <= sum([model.pb[i,j] for i in model.V])
    
    def only_existing_edges(model, i, j):
        return model.p[i,j] <= model.E[i,j]

    def only_existing_edgesb(model, i, j):
        return model.pb[i,j] <= model.E[i,j]
    
    def only_one_direction(model, i, j):
        return model.p[i,j] + model.p[j,i] <= 1

    def only_one_directionb(model, i, j):
        return model.pb[i,j] + model.pb[j,i] <= 1
    
    def separate_trees(model, i, j):
        return model.p[j,i] + model.pb[j,i] + model.p[i,j] + model.pb[i,j] <= 1

    print('Building the L2 Multigraph model')
    
    model.OBJ = pyo.Objective(rule=objective)
    
    model.distance = pyo.Constraint(model.V, rule=dist_c)
    model.distanceb = pyo.Constraint(model.V, rule=dist_cb)
    model.one_incoming = pyo.Constraint(model.V, rule=one_incoming)
    model.one_incomingb = pyo.Constraint(model.V, rule=one_incomingb)
    if max_out_deg > 0:
        model.deg = max_out_deg
        model.max_deg = pyo.Constraint(model.V, rule=max_deg)
        model.max_degb = pyo.Constraint(model.V, rule=max_degb)
    elif max_out_deg < 0: 
        model.deg = -max_out_deg
        model.max_deg = pyo.Constraint(model.V, model.D, rule=max_deg_decr)
        model.max_degb = pyo.Constraint(model.V, model.D, rule=max_deg_decrb)

    model.incremental_distance = pyo.Constraint(model.V, model.V, model.D_pos, 
                                       rule=incremental_distance)
    model.incremental_distanceb = pyo.Constraint(model.V, model.V, model.D_pos, 
                                       rule=incremental_distanceb)
    model.distance_incoming = pyo.Constraint(model.V, rule=distance_implies_incoming)
    model.distance_incomingb = pyo.Constraint(model.V, rule=distance_implies_incomingb)
    model.only_existing_edges = pyo.Constraint(model.V, model.V, 
                                       rule=only_existing_edges)
    model.only_existing_edgesb = pyo.Constraint(model.V, model.V, 
                                       rule=only_existing_edgesb)
    model.unidirectional = pyo.Constraint(model.V, model.V, 
                                       rule=only_one_direction)    
    model.unidirectionalb = pyo.Constraint(model.V, model.V, 
                                       rule=only_one_directionb)    
    model.separate_trees = pyo.Constraint(model.V, model.V, 
                                       rule=separate_trees) 
    
    return model


def make_l2_model(model, nodes, edges, max_diam, max_out_deg=0):
    model.D = pyo.RangeSet(0, max_diam)
    model.D_pos = pyo.RangeSet(1, max_diam)
    model.V = pyo.Set(initialize=nodes)


    
    def edge_init(model, i, j):
        return (i,j) in edges
    
    model.E = pyo.Param(model.V, model.V, initialize=edge_init, 
                        domain=pyo.Binary)
    model.u = pyo.Var(model.V, model.D, domain=pyo.Binary, initialize=0)
    model.p = pyo.Var(model.V, model.V, domain=pyo.Binary, initialize=0)
 
    
    def objective(model):
        return sum([model.u[i,0] for i in model.V])
    
    def dist_c(model,i):
        return sum([model.u[i,l] for l in model.D]) == 1
    
    def one_incoming(model, j):
        return sum([model.p[i,j] for i in model.V]) == 1 - model.u[j,0]
    

    def max_deg(model, i):
        return sum([model.p[i,j] for j in model.V]) <= model.deg
    
    def max_deg_decr(model, i, j):
        return sum([model.p[i,k] for k in model.V]) <= model.deg - j*model.u[i,j] 
    
    def incremental_distance(model, i, j, l):
        return model.p[i,j] <= 1 - model.u[j,l] + model.u[i,l-1]
        
    def distance_implies_incoming(model, j):
        return sum([model.u[j,l] for l in model.D_pos]) <= sum([model.p[i,j] for i in model.V])
    
    def only_existing_edges(model, i, j):
        return model.p[i,j] <= model.E[i,j]
    
    def only_one_direction(model, i, j):
        return model.p[i,j] + model.p[j,i] <= 1
   
    print('Building the L2 model')
    
    model.OBJ = pyo.Objective(rule=objective)
    
    model.distance = pyo.Constraint(model.V, rule=dist_c)
    model.one_incoming = pyo.Constraint(model.V, rule=one_incoming)
    if max_out_deg > 0:
        model.deg = max_out_deg
        model.max_deg = pyo.Constraint(model.V, rule=max_deg)
    elif max_out_deg < 0: 
        model.deg = -max_out_deg
        model.max_deg = pyo.Constraint(model.V, model.D, rule=max_deg_decr)

    model.incremental_distance = pyo.Constraint(model.V, model.V, model.D_pos, 
                                       rule=incremental_distance)
    model.distance_incoming = pyo.Constraint(model.V, rule=distance_implies_incoming)
    model.only_existing_edges = pyo.Constraint(model.V, model.V, 
                                       rule=only_existing_edges)
    model.unidirectional = pyo.Constraint(model.V, model.V, 
                                       rule=only_one_direction)    
    return model


def make_flow_model(model, capacity_dict=10, demand_dict=1):
 
    # if capacity_dict and demand_dict are dictionaries with 
    # nodes as keys, this still works
    model.capacity = pyo.Param(model.V, initialize=capacity_dict, 
                               domain=pyo.PositiveIntegers)
    model.demand = pyo.Param(model.V, initialize=demand_dict,
                             domain=pyo.NonNegativeIntegers)
    model.f = pyo.Var(model.V, model.V, model.V, 
                      domain=pyo.NonNegativeIntegers, initialize=0)
    
    
    def capacity_limit(model, i):
        return sum([model.f[i,j,h] for j in model.V for h in model.V]) \
               <= model.capacity[i]
    
    def flow_conservation(model, i):
        return sum([model.f[i,j,h] for j in model.V for h in model.V if i!=h])\
               - \
               sum([model.f[j,i,h] for j in model.V for h in model.V if i!=h])\
               == model.u[i,0]*model.capacity[i]
               
    def flow_demand(model, j):
        return sum([model.f[i,j,j] for i in model.V]) >= \
               (1-model.u[j,0])*model.demand[j]
    
    def no_outgoing_flow(model, i, j):
        return model.f[i,j,i] == 0
    
    def selected_edges_only(model, i, j, h):
        return model.f[i,j,h] <= model.p[i,j]*model.capacity[i]

    print('Building the flow model')

    model.capacity_limit = pyo.Constraint(model.V, rule=capacity_limit)
    model.flow_conservation = pyo.Constraint(model.V, rule=flow_conservation)
    model.flow_demand = pyo.Constraint(model.V, rule=flow_demand)
    model.no_outgoing = pyo.Constraint(model.V, model.V, 
                                        rule=no_outgoing_flow)
    model.only_selected_edges = pyo.Constraint(model.V, model.V, model.V, 
                                        rule=selected_edges_only)
    return model
