import os, json, csv
import gurobipy as gp
from gurobipy import GRB
from gurobipy import quicksum


# Location Data
# Object Fields
# {
#   "loc_id": 1.0,
#   "title": "Amherst Survival Center",
#   "type": "Agency",
#   "street1": "138 Sunderland Road",
#   "city": "Amherst",
#   "zip": "01002",
#   "state": "MA",
#   "long": -72.53289,
#   "lat": 42.41472
# }

locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"] != "Pick-up"] # 125 locations
locations = locations[:50]
N_LOCS = len(locations) + 1 # all delivery locatoins + warehouse start/end
O = 0
D = N_LOCS-1
Q = 12
K = N_LOCS // 3

# Assume that all the vehicles are the same
# k is the number of runs, lets set k=# of locations (overshoot) so we don't have to worry about the variable

# Distance Matrix
# 137x137 Matrix - Distances stored as Meters (ignore the final 12 rows and cols)
distances_matrix = json.load(open(os.path.abspath("./data/distances_matrix.json"), "r"))

# Travel Times Matrix
# 137x137 Matrix - Time travelled stored as Seconds
c = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))

demands = [0]
with open("data/FBWMLocationsDemands.csv") as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
    if len(demands) >= N_LOCS-1: break
    if line_count == 0 or line_count == 1:
      line_count += 1
      continue
    # TODO: handle decimal delivery quantities
    else:
      demands.append(int(row[6][0]))
      if demands[-1] == 0: demands[-1] = 1
    line_count += 1
demands.append(0)

# MODEL
m = gp.Model()

# VARIABLES
# x_ijk = 1 if run #k goes from i to k
x = m.addVars(N_LOCS, N_LOCS, K, vtype=GRB.BINARY, name="x")
# y_ik = 1 if location i is on route k
y = m.addVars(N_LOCS, K, vtype=GRB.BINARY, name="y")
# u_ik = amt delivered by route k to location i
u = m.addVars(N_LOCS, K, vtype=GRB.INTEGER, lb=0, ub=10, name='u')

# OBJECTIVE FUNCTION
objective = quicksum(x[i, j, k] * c[i][j] for i in range(N_LOCS) for j in range(N_LOCS) for k in range(K))
for i in range(N_LOCS):
	for j in range(N_LOCS):
		for k in range(K):
			objective += x[i, j, k] * c[i][j]
m.setObjective(objective, GRB.MINIMIZE)

# RUN-TIME SPEEDUP
# try using gurobipy.quicksum instead of sum
m.params.MIPFocus=1

# CONSTRAINTS
# 1.9: every location (not depot) visited exactly once
for i in range(1, N_LOCS-1):
  lhs = 0
  for k in range(K):
    lhs += y[i, k]
  m.addConstr(lhs == 1)
# 1.10.1: every location (not depot) left exactly once
for i in range(1, N_LOCS-1):
  lhs = 0
  for j in range(1, N_LOCS):
    for k in range(K):
      lhs += x[i, j, k]
  m.addConstr(lhs == 1)
# 1.10.2: every location (not depot) entered exactly once
for i in range(1, N_LOCS-1):
  lhs = 0
  for j in range(0, N_LOCS-1):
    for k in range(K):
      lhs += x[j, i, k]
  m.addConstr(lhs == 1)
# 1.10.3: the start depot is left once in each run
for k in range(K):
  lhs = 0
  for j in range(1, N_LOCS):
    lhs += x[O, j, k]
  m.addConstr(lhs == 1)
# 1.10.4: the end depot is entered once in each run
for k in range(K):
  lhs = 0
  for i in range(N_LOCS-1):
    lhs += x[i, D, k]
  m.addConstr(lhs == 1)
# sum of the ways into it minus the ways out is 0
for k in range(K):
  for i in range(1, N_LOCS-1):
    ways_in = quicksum(x[j, i, k] for j in range(N_LOCS-1))
    ways_out = quicksum(x[i, j, k] for j in range(1, N_LOCS))
    m.addConstr(ways_in - ways_out == 0)


# 1.11: for all the locations, y_ik = 1 if we leave the location (x[i, j, k] = 1)
for i in range(1, N_LOCS-1):
  for k in range(K):
    rhs = 0
    for j in range(1, N_LOCS):
      rhs += x[i, j, k]
    m.addConstr(y[i, k] == rhs)

# 1.12: y_ok and y_dk = 1 always
for k in range(K):
  m.addConstr(y[O, k] == 1)
  m.addConstr(y[D, k] == 1)

#1.13: MTZ-Specific SEC
for i in range(1, N_LOCS-1):
  for j in range(1, N_LOCS-1):
    if i == j: continue
    for k in range(K):
      m.addConstr(u[i, k] - u[j, k] + Q*x[i, j, k] <= Q - demands[j])

# 1.14: capacity constraints
for i in range(N_LOCS):
  for k in range(K):
    m.addConstr(demands[i] <= u[i,k])
    m.addConstr(u[i,k] <= Q)

# 2.1: no self-loops
for k in range(K):
  for i in range(N_LOCS):
    m.addConstr(x[i, i, k] == 0)

# Solve the LP
print("OPTIMIZING")
m.optimize()
print("FINISHED")

#for v in m.getVars():
#  if (v.varName[0] == "x"):
#    print(v.varName, v.x, end = " | ")

for k in range(K):
  print("K =", k)
  for i in range(N_LOCS):
    for j in range(N_LOCS):
      if x[i, j, k].x == 1:
        print(str(i) + " -> " + str(j) + " | ui = " + str(u[i, k].x))
      
pass
# TODO:
# check capacity constraints
# make paths:
#   if u enter a loc, u must leave that loc (unless the last)
#   if u leave a loc, u must enter that loc (unless the first)