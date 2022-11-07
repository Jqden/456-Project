import os, json, csv
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

N = 8
locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"] != "Pick-up"] # 125 locations
x = [(loc["long"], loc["lat"]) for loc in locations]
x = x[1:] # don't fit the depot

kmeans = KMeans(n_clusters=N, random_state=0).fit(x)
identified_clusters = kmeans.fit_predict(x)
clusters = {"long": [xy[0] for xy in x], "lat": [xy[1] for xy in x], "clusters": identified_clusters}

#plt.scatter(clusters['long'],clusters['lat'],c=clusters['clusters'],cmap='rainbow')
#plt.scatter((locations[0]["long"], ), locations[0]["lat"])
#plt.axis('equal')
#plt.show()

costs = json.load(open(os.path.abspath("./data/travel_times_matrix.json"), "r"))
demands = [0]
with open("data/FBWMLocationsDemands.csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if len(demands) >= len(locations)-1: break
        if line_count == 0 or line_count == 1:
            line_count += 1
            continue
        else:
            demands.append(int(row[6][0]))
            if demands[-1] == 0: demands[-1] = 1
        line_count += 1
demands.append(0)

clusters = clusters["clusters"]
locs_0 = [locations[0]]
costs_0 = [costs[0]]
dems_0 = [0]
for i, cluster in enumerate(clusters):
    if cluster == 0:
        locs_0.append(locations[i+1])
        costs_0.append(costs[i+1])
        dems_0.append(demands[i+1])
dems_0.append(0)

for i, cs in enumerate(costs_0[:len(locations)+1]):
    new_cs = []
    for j, cost in enumerate(cs):
        if j == len(locations):
            new_cs.append(new_cs[0])
            break
        elif clusters[j] == 0:
            new_cs.append(cost)
    costs_0[i] = new_cs
costs_0.append(costs_0[0])