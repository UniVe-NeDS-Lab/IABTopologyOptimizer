# An ILP model to choose the best backhaul topology for a 5G IAB network


# Requirements:

 - The Pyomo Python3 library to build ILP models
 - A solver (glpk by default)
 - networkx library to parse the backhaul graphs

# Principle

Assuming g is a directed connected network graph representing the feasible links in a network, this program will choose:
 
 - the number of donors
 - the tree connecting each donor to a subset of the network graph 

So that each node in the network is part of a distribution tree, and the number of distribution trees are minimized.

The constraints that can be posed are:

 - a limited number of outgoing edges per node
 - enough flow going from the donor to the gNS
 - a limited tree height

It will produce results in two .log files and a graph.png showing the solution.

In the following image you can see a 32 nodes network, where red nodes are the chosen donors, blue nodes are the gNB, black links are the links of the three distribution tree and gray ones are the possible links in the original connectivity graph.

<img src="graph-example.png" alt="example network" width="400" align="center"/>