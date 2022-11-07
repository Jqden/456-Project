import os, json
import gurobipy as gp
import matplotlib.pyplot as plt
from gurobipy import GRB
from gurobipy import quicksum
import utility_final as utility

# STEP 1: PROCESS THE DATA
# Locations data and constants
locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"]
             != "Pick-up"]  # 125 locations
#locations = locations[:15]
subsets = utility.get_subsets2(locations, 4)
N_LOCS = len(locations) + 1  # all delivery locations + warehouse start/end
O = 0
D = N_LOCS-1
Q = 12

# The cost matrix (travel times)
c = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))
c = c[:N_LOCS]
for i, lst in enumerate(c):
    lst[D] = lst[0]  # fix it so that D has same cost as O
# Demands matrix
demands = utility.get_demands(N_LOCS)
routes = []

for subset in subsets:
    # MODEL
    m = gp.Model()

    # VARIABLES
    # x_ijk = 1 if run #k goes from i to k
    x = m.addVars(N_LOCS, N_LOCS, vtype=GRB.BINARY, name="x")
    # u_ik = amt delivered by route k to location i
    u = m.addVars(N_LOCS, vtype=GRB.INTEGER, lb=0, ub=10, name='u')
    # k = number of routes
    k = m.addVar(vtype=GRB.INTEGER, name = 'k')

    # OBJECTIVE FUNCTION
    objective = quicksum(x[i, j] * c[i][j] for i in subset for j in subset)
    m.setObjective(objective, GRB.MINIMIZE)

    # RUN-TIME OPTIMIZATIONS
    m.params.MIPFocus=1 # 2 or 3 don't seem to get faster

    # CONSTRAINTS
    # 1.1 every location (excluding depot) left exactly once
    for i in subset[1:-1]:
        lhs = 0
        for j in subset[1:]:
            lhs += x[i, j]
        m.addConstr(lhs == 1)
    # 1.2: every location (excluding depot) entered exactly once
    for i in subset[1:-1]:
        lhs = 0
        for j in subset[:-1]:
            lhs += x[j, i]
        m.addConstr(lhs == 1)
    # 1.3: the start depot is left exactly K times
    lhs1 = quicksum(x[O, j] for j in subset[1:])
    m.addConstr(lhs1 == k)
    # 1.4: the end depot is entered exactly K times
    lhs2 = quicksum(x[i, D] for i in subset[:-1])
    m.addConstr(lhs2 == k)

    # 2.1: MTZ-Specific SEC
    for i in subset[1:-1]:
        for j in subset[1:-1]:
            if i == j: continue
            m.addConstr(u[i] - u[j] + Q*x[i, j] <= Q - demands[j])

    # 2.2: capacity constraints
    for i in subset:
        m.addConstr(demands[i] <= u[i])
        m.addConstr(u[i] <= Q)

    # 2.1: no self-loops
    for i in subset[1:-1]:
        m.addConstr(x[i, i] == 0)

    # Solve the LP
    m.optimize()

    for i in range(1, N_LOCS):
        if x[O, i].x == 1:
            left = i
            route = [O, i]
            while left != D:
                for right in range(1, N_LOCS):
                    if x[left, right].x == 1:
                        route.append(right)
                        left = right
                        break
            routes.append(route)

# STEP 3.2: VISUALIZE THE ROUTES
color_cycle = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
color_i = 0
for route in routes:
    for i, j in zip(route[:-1], route[1:]):
        i = i if i != D else 0
        j = j if j != D else 0
        xs = (locations[i]["long"], locations[j]["long"])
        ys = (locations[i]["lat"], locations[j]["lat"])
        plt.plot(xs, ys, color=color_cycle[color_i])
    color_i = (color_i + 1) % len(color_cycle)

plt.axis('equal')
plt.legend()
plt.show()

pass