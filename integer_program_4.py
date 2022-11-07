import os, json
import gurobipy as gp
import matplotlib.pyplot as plt
from gurobipy import GRB
from gurobipy import quicksum
import utility_final as utility


"""
This integer program finds an optimal set of routes to send trucks carrying food
pallets out to service 124 locations. Each truck can carry 12 pallets, and each
location has an integer number of required pallets between 0 and 12. Every route
must begin and end at the depot.
"""

# Acquire locations data
locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"] != "Pick-up"]
# locations[0] holds the depot's information

"""
Each path starts and ends at the depot. Our integer program declares both a
start depot "O" and an end depot "D", which are actually the same location.
Thus, our integer program is finding routes from O-D that go through drop-off
locations such that we deliver to all drop-off locations as fast as possible
without violating any constraints.
"""

# Declare Constants
N_LOCS = len(locations) + 1 # N_LOCS = start depot + drop-off locations + end depot
O = 0 # the start (depot)
D = N_LOCS-1 # the end (depot)
Q = 12 # number of pallets a truck can hold

# Acquire cost matrix (travel times in seconds betewen every location)
# c[i,j] is the cost of going from location i to location j
c = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))
c = c[:N_LOCS]
for i, lst in enumerate(c):
    lst[D] = lst[0]  # fix it so that i to D has same cost as i to O

# Demands matrix
# demands[i] is the required pallets of location i (0 for the depot)
demands = utility.get_demands(N_LOCS)


m = gp.Model()

# VARIABLES
# x[i,j] = 1 if a truck goes from location i to location j
x = m.addVars(N_LOCS, N_LOCS, vtype=GRB.BINARY, name="x")
# u[i] = amount of pallets delivered to location i
u = m.addVars(N_LOCS, vtype=GRB.INTEGER, lb=0, ub=10, name='u')
# k = total number of routes to satisfy all locations
k = m.addVar(vtype=GRB.INTEGER, name = 'k')

# OBJECTIVE FUNCTION
objective = quicksum(x[i, j] * c[i][j] for i in range(N_LOCS) for j in range(N_LOCS))
m.setObjective(objective, GRB.MINIMIZE)

# RUN-TIME OPTIMIZATIONS
m.params.MIPFocus=1 # 2 and 3 seem to be marginally slower

# CONSTRAINTS
# 1.1: every location (excluding depot) left exactly once
for i in range(1, N_LOCS-1):
    lhs = 0
    for j in range(1, N_LOCS):
        lhs += x[i, j]
    m.addConstr(lhs == 1)
# 1.2: every location (excluding depot) entered exactly once
for i in range(1, N_LOCS-1):
    lhs = 0
    for j in range(0, N_LOCS-1):
        lhs += x[j, i]
    m.addConstr(lhs == 1)
# 1.3: the start depot is left exactly K times
lhs1 = quicksum(x[O, j] for j in range(1, N_LOCS))
m.addConstr(lhs1 == k)
# 1.4: the end depot is entered exactly K times
lhs2 = quicksum(x[i, D] for i in range(N_LOCS-1))
m.addConstr(lhs2 == k)


# 2.1: MTZ-Specific Subtour Elimination Constraints
for i in range(1, N_LOCS-1):
  for j in range(1, N_LOCS-1):
    if i == j: continue
    m.addConstr(u[i] - u[j] + Q*x[i, j] <= Q - demands[j])

# 2.2: capacity constraints
for i in range(N_LOCS):
    m.addConstr(demands[i] <= u[i])
    m.addConstr(u[i] <= Q)

# 2.1: no self-loops
for i in range(N_LOCS):
    m.addConstr(x[i, i] == 0)

# Solve the LP
m.optimize()

# RESULTS
routes = utility.build_routes(x, N_LOCS, O, D)
print(",\n".join(str(route) for route in routes))
utility.plot_all_routes(routes, locations)
utility.plot_4_groups_of_routes(routes, locations)
utility.print_routes(routes, demands)