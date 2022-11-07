import os, json, csv
import gurobipy as gp
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
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

# Get locations data
locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"] != "Pick-up"] # 125 locations

# Find subsets from locations using kmeans
x = [(loc["long"], loc["lat"]) for loc in locations]
x = x[1:] # don't fit the depot
N_CLUSTERS = 8
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(x)
identified_clusters = kmeans.fit_predict(x)
subsets = [[0] for _ in range(N_CLUSTERS)]
for i, cluster in enumerate(identified_clusters):
    subsets[cluster].append(i+1)
for i in range(N_CLUSTERS):
    subsets[i].append(len(locations))

#locations = locations[:15]

N_LOCS = len(locations) + 1 # all delivery locations + warehouse start/end
O = 0
D = N_LOCS-1
Q = 12
K = N_LOCS // 2

# Assume that all the vehicles are the same
# k is the number of runs, we need to overestimate w/ K to guarantee
# optimal solutions.

# Get travel times matrix
c = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))
c = c[:N_LOCS]
for i, lst in enumerate(c):
    lst[D] = lst[0] # the depot is stored twice: once at o (0) and once at D (len(locations))

# Get demands matrix
demands = [0]
with open("data/FBWMLocationsDemands.csv") as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
    if len(demands) >= N_LOCS-1: break
    if line_count == 0 or line_count == 1:
      line_count += 1
      continue
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

subset = subsets[1]
# OBJECTIVE FUNCTION
objective = quicksum(x[i, j, k] * c[i][j] for i in subset for j in subset for k in range(K))
m.setObjective(objective, GRB.MINIMIZE)

# RUN-TIME OPTIMIZATIONS
m.params.MIPFocus=1 # 2 or 3 don't seem to get faster

# CONSTRAINTS
# 1.9: every location (not depot) visited exactly once
for i in subset[1:-1]: # exclude start depot and end depot
  lhs = 0
  for k in range(K):
    lhs += y[i, k] #+=y[subsetlocations[i],k]
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
    if i == j: continue
    for k in range(K):
      m.addConstr(u[i, k] - u[j, k] + Q*x[i, j, k] <= Q - demands[j])

# 1.14: capacity constraints
for i in subset:
  for k in range(K):
    m.addConstr(demands[i] <= u[i,k])
    m.addConstr(u[i,k] <= Q)

# 2.1: no self-loops
for k in range(K):
  for i in subset:
    m.addConstr(x[i, i, k] == 0)

# 2.2: set unused variables to 0
for i in range(N_LOCS):
    if i not in subset:
        for k in range(K):
            m.addConstr(y[i,k] == 0)
            m.addConstr(u[i,k] == 0)
        for j in range(N_LOCS):
            if j not in subset:
                for k in range(K):
                    m.addConstr(x[i,j,k] == 0)

# Solve the LP
print("OPTIMIZING")
m.optimize()
print("FINISHED")


routes = []
for k in range(K):
  route = []
  print("K =", k)
  for i in range(N_LOCS):
    for j in range(N_LOCS):
      if x[i, j, k].x == 1:
        route.append((i, j))
        print(str(i) + " -> " + str(j) + " | ui = " + str(u[i, k].x))
  if len(route) != 1: routes.append(route)

for i, route in enumerate(routes):
    for line in route:
        e1 = line[0]
        e2 = line[1]
        if e1 == N_LOCS-1: e1 = 0
        if e2 == N_LOCS-1: e2 = 0
        a = (locations[e1]["long"], locations[e2]["long"])
        b = (locations[e1]["lat"], locations[e2]["lat"])
        plt.plot(a, b, color='b')        
plt.axis('equal')
plt.legend()
plt.show()