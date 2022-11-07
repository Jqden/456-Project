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

#clusters = {"long": [xy[0] for xy in x], "lat": [xy[1] for xy in x], "clusters": identified_clusters}
#plt.scatter(clusters['long'],clusters['lat'],c=clusters['clusters'],cmap='rainbow')
#plt.scatter((locations[0]["long"], ), locations[0]["lat"])
#plt.axis('equal')
#plt.show()

subsets = [[0] for _ in range(N)]
for i, cluster in enumerate(identified_clusters):
    subsets[cluster].append(i+1)
for i in range(N):
    subsets[i].append(len(locations))