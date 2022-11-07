import matplotlib.pyplot as plt
import os, json

locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"] != "Pick-up"] # 125 locations
locations = locations[:20]
N_LOCS = len(locations) + 1 # all delivery locatoins + warehouse start/end
O = 0
D = N_LOCS-1
Q = 12
K = N_LOCS // 2

routes = [[(0, 16), (7, 17), (8, 13), (13, 20), (16, 7), (17, 8)], 
    [(0, 15), (5, 9), (9, 14), (14, 20), (15, 18), (18, 5)], 
    [(0, 1), (1, 3), (2, 20), (3, 12), (12, 2)], 
    [(0, 10), (10, 20)], 
    [(0, 6), (4, 19), (6, 4), (11, 20), (19, 11)]]

colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

for i, route in enumerate(routes):
    color = colors.pop()
    for line in route:
        e1 = line[0]
        e2 = line[1]
        if e1 == 20: e1 = 0
        if e2 == 20: e2 = 0
        a = (locations[e1]["long"], locations[e2]["long"])
        b = (locations[e1]["lat"], locations[e2]["lat"])
        plt.plot(a, b, color)        
plt.axis('equal')
plt.legend()
plt.show()