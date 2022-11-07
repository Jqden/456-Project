import csv
from posixpath import split
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import math


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

def build_routes(x, N_LOCS, O, D):
    routes = []
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
    return routes

def plot_all_routes(routes, locations):
    fig, ax = plt.subplots()
    ax.set_title("All Routes")

    for route in routes:
        route[-1] = 0
        xs = [locations[i]["long"] for i in route]
        ys = [locations[i]["lat"] for i in route]
        ax.plot(xs, ys)
    ax.axis('equal')
    plt.show()

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def plot_4_groups_of_routes(routes, locations):
    fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)
    route_groups = list(split(routes, 4))
    fig.suptitle("4 Evenly Sized Groups of Routes")

    for plot_i, routes in enumerate(route_groups):
        for route in routes:
            route[-1] = 0
            xs = [locations[i]["long"] for i in route]
            ys = [locations[i]["lat"] for i in route]
            axs[plot_i % 2, plot_i // 2].plot(xs, ys)
    plt.show()

def print_routes(routes, demands):
    routes.sort(key = len)
    print(f"Total routes: {len(routes)}")
    print("Locations Satisfied | Pallets Deliverd | Path")
    for route in routes:
        pallets_delivered = sum(demands[i] for i in route)
        route = [str(r) for r in route]
        route[0] = "O"
        route[-1] = "D"
        path = " -> ".join(route)
        locs_satisfied = len(route) - 2

        print(f"{locs_satisfied} | {pallets_delivered:02} | {path}")

# The following functions are used for integer_program_5.py, which uses
# kmeans

# STRATEGY 1
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


# STRATEGY 2
# use kmeans to recursively split the group of locations into
# two clusters, than recurse on a cluster if it is larger than
# 40 locations
def get_kmeans(locations):
    x = [(loc["long"], loc["lat"]) for loc in locations]
    x = x[1:] # don't fit the depot

    subsets = []
    recurse_kmeans(x, subsets)
    depot = (locations[0]["long"], locations[0]["lat"])
    plot_subsets_and_depot(subsets, depot)

    return subsets

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


# For visualizing results of subsets
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
