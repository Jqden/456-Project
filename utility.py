import csv
from posixpath import split
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import math

# split xy_locs into two groupings
# recurse on a grouping of size greater than 40
# return all groupings as a list of list of xy_locs
def recurse_kmeans(xy_locs, res):
    kmeans = KMeans(n_clusters=2, random_state=0).fit(xy_locs)
    identified_clusters = kmeans.fit_predict(xy_locs)

    subsets = [[], []]
    for location, cluster in zip(xy_locs, identified_clusters):
        subsets[cluster].append(location)
    
    for subset in subsets:
        if len(subset) <= 40:
            res.append(subset)
        else:
            recurse_kmeans(subset, res)

# return an identified clusters list
def get_kmeans(locations):
    x = [(loc["long"], loc["lat"]) for loc in locations]
    x = x[1:] # don't fit the depot

    subsets = []
    recurse_kmeans(x, subsets)
    depot = (locations[0]["long"], locations[0]["lat"])
    plot_subsets_and_depot(subsets, depot)

    return subsets

def plot_subsets_and_depot(subsets, depot):
    # unpack the subsets
    graph_info = {"long": [], "lat": [], "cluster": []}
    for i, subset in enumerate(subsets):
        for location in subset:
            graph_info["long"].append(location[0])
            graph_info["lat"].append(location[1])
            graph_info["cluster"].append(i)

    # plot the unpacked subsets
    plt.scatter(graph_info['long'], graph_info['lat'], c=graph_info['cluster'],cmap='rainbow')
    plt.scatter(depot[0], depot[1])
    plt.axis('equal')
    plt.show()
    pass

# do a simple kmeans to get N_CLUSTERS clusters
def get_subsets2(locations, N_CLUSTERS):
    x = [(loc["long"], loc["lat"]) for loc in locations]
    x = x[1:] # don't fit the depot

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(x)
    identified_clusters = kmeans.fit_predict(x)

    subsets = [[] for _ in range(N_CLUSTERS)]
    for i, cluster in enumerate(identified_clusters):
        subsets[cluster].append(i+1)
    
    return [[0] + r + [len(locations)] for r in subsets]

# Finds N_CLUSTERS subsets of locations using K-Means
def get_subsets(locations, N_CLUSTERS):
    x = [(loc["long"], loc["lat"]) for loc in locations]
    x = x[1:] # don't fit the depot

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(x)
    identified_clusters = kmeans.fit_predict(x)

    #clusters = {"long": [xy[0] for xy in x], "lat": [xy[1] for xy in x], "clusters": identified_clusters}
    #plt.scatter(clusters['long'],clusters['lat'],c=clusters['clusters'],cmap='rainbow')
    #plt.scatter((locations[0]["long"], ), locations[0]["lat"])
    #plt.axis('equal')
    #plt.show()

    subsets = [[] for _ in range(N_CLUSTERS)]
    for i, cluster in enumerate(identified_clusters):
        subsets[cluster].append(i+1)
    
    res = []
    for subset in subsets:
        if len(subset) > 10:
            chunks = list(split(subset, math.ceil(len(subset) / 10)))
            res += chunks
        else:
            res += [subset]

    res = [[0] + r + [len(locations)] for r in res]

    return res

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def get_demands(N_LOCS):
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
    return demands