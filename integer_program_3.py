import os
import json
import csv
import gurobipy as gp
import matplotlib.pyplot as plt
from gurobipy import GRB
from gurobipy import quicksum
import utility

"""
There are 125 dropoff locations. N_LOCS is 126 because we count the depot
twice in our simulation, once at the start (variable O) and once at the 
end (variable D). Thus, the integer programs job is to find paths from
O to D that satisfy all the constraints and minimize cost.

We are finding K O-D paths such that we minimize the path cost. We
overestimate K so that we are guaranteed to get enough routes. This means
we generate some "unused" paths, which are represented by a direct path
from O-D.

The program cannot run on all 125 locations simultaneously. So, we split
the work up into several runs on smaller subsets of locations using
K-Means to generate these subsets.
"""

# STEP 1: PROCESS THE DATA
# Locations data and constants
locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"]
             != "Pick-up"]  # 125 locations
N_LOCS = len(locations) + 1  # all delivery locations + warehouse start/end
O = 0
D = N_LOCS-1
Q = 12

# Find 8 nearby subsets of locations using kmeans
subsets = utility.get_subsets(locations, 8)
# The cost matrix (travel times)
c = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))
c = c[:N_LOCS]
for i, lst in enumerate(c):
    lst[D] = lst[0]  # fix it so that D has same cost as O
# Demands matrix
demands = utility.get_demands(N_LOCS)
routes = []


# STEP 2: RUN INTEGER PROGRAM ON EACH SUBSET
for set_num, subset in enumerate(subsets):
    K = len(subset)
    print("Processing set number " + str(set_num) + " with " + str(len(subset)) + " locations.")
    # MODEL
    m = gp.Model()

    # VARIABLES
    # x_ijk = 1 if route #k goes from i to j
    x = m.addVars(N_LOCS, N_LOCS, K, vtype=GRB.BINARY, name="x")
    # y_ik = 1 if location i is on route k
    y = m.addVars(N_LOCS, K, vtype=GRB.BINARY, name="y")
    # u_ik = amt delivered by route k to location i
    u = m.addVars(N_LOCS, K, vtype=GRB.INTEGER, lb=0, ub=10, name='u')

    # OBJECTIVE FUNCTION
    objective = quicksum(x[i, j, k] * c[i][j]
                        for i in subset for j in subset for k in range(K))
    m.setObjective(objective, GRB.MINIMIZE)


    # RUN-TIME OPTIMIZATIONS
    m.params.MIPFocus = 1  # 2 or 3 don't seem to get faster

    # CONSTRAINTS
    # 1.9: every location (not depot) visited exactly once
    for i in subset[1:-1]:  # exclude start depot and end depot
        lhs = 0
        for k in range(K):
            lhs += y[i, k]  # +=y[subsetlocations[i],k]
        m.addConstr(lhs == 1)
    # 1.10.1: every location (not depot) left exactly once
    for i in subset[1:-1]:
        lhs = 0
        for j in subset[1:]:
            for k in range(K):
                lhs += x[i, j, k]
        m.addConstr(lhs == 1)
    # 1.10.2: every location (not depot) entered exactly once
    for i in subset[1:-1]:
        lhs = 0
        for j in subset[:-1]:
            for k in range(K):
                lhs += x[j, i, k]
        m.addConstr(lhs == 1)
    # 1.10.3: the start depot is left once in each run
    for k in range(K):
        lhs = 0
        for j in subset[1:]:
            lhs += x[O, j, k]
        m.addConstr(lhs == 1)
    # 1.10.4: the end depot is entered once in each run
    for k in range(K):
        lhs = 0
        for i in subset[:-1]:
            lhs += x[i, D, k]
        m.addConstr(lhs == 1)
    # sum of the ways into it minus the ways out is 0
    for k in range(K):
        for i in subset[1:-1]:
            ways_in = quicksum(x[j, i, k] for j in subset[:-1])
            ways_out = quicksum(x[i, j, k] for j in subset[1:])
            m.addConstr(ways_in - ways_out == 0)


    # 1.11: for all the locations, y_ik = 1 if we leave the location (x[i, j, k] = 1)
    for i in subset[1:-1]:
        for k in range(K):
            rhs = 0
            for j in subset[1:]:
                rhs += x[i, j, k]
            m.addConstr(y[i, k] == rhs)

    # 1.12: y_ok and y_dk = 1 always
    for k in range(K):
        m.addConstr(y[O, k] == 1)
        m.addConstr(y[D, k] == 1)

    #1.13: MTZ-Specific SEC
    for i in subset[1:-1]:
        for j in subset[1:-1]:
            if i == j:
                continue
            for k in range(K):
                m.addConstr(u[i, k] - u[j, k] + Q*x[i, j, k] <= Q - demands[j])

    # 1.14: capacity constraints
    for i in subset:
        for k in range(K):
            m.addConstr(demands[i] <= u[i, k])
            m.addConstr(u[i, k] <= Q)

    # 2.1: no self-loops
    for k in range(K):
        for i in subset:
            m.addConstr(x[i, i, k] == 0)

    # 2.2: set unused variables to 0
    for i in range(N_LOCS):
        if i not in subset:
            for k in range(K):
                m.addConstr(y[i, k] == 0)
                m.addConstr(u[i, k] == 0)
            for j in range(N_LOCS):
                if j not in subset:
                    for k in range(K):
                        m.addConstr(x[i, j, k] == 0)

    # Solve the LP
    m.optimize()

    # Record the optimal routes
    subset_routes = []
    for k in range(K):
        route = []
        for i in range(N_LOCS):
            for j in range(N_LOCS):
                if x[i, j, k].x == 1:
                    route.append((i, j))
        if len(route) != 1:
            subset_routes.append(route)
    routes.append(subset_routes)
    print("Found " + str(len(subset_routes)) + " routes to satisfy subset")
print()
print()

# STEP 3.1: PRINT THE ROUTES
print("THE ROUTES:")
new_routes = []
for subset_routes in routes:
    new_sr = []
    for route in subset_routes:
        new_r = []
        loc = O
        while loc != D:
            for edge in route:
                if edge[0] == loc:
                    new_r.append(loc)
                    loc = edge[1]
                    break
        new_r.append(D)
        new_sr.append(new_r)
    new_routes.append(new_sr)
for subset_routes in new_routes:
    for route in subset_routes:
        route = [str(e) for e in route]
        path = " -> ".join(route)
        print(path)

# STEP 3.2: VISUALIZE THE ROUTES
color_cycle = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
color_i = 0
for subset_routes in routes:
    for route in subset_routes:
        for edge in route:
            e1 = edge[0] if edge[0] != D else 0
            e2 = edge[1] if edge[1] != D else 0
            xs = (locations[e1]["long"], locations[e2]["long"])
            ys = (locations[e1]["lat"], locations[e2]["lat"])
            plt.plot(xs, ys, color=color_cycle[color_i])
    color_i = (color_i + 1) % len(color_cycle)

plt.axis('equal')
plt.legend()
plt.show()