import matplotlib.pyplot as plt
import os, json
import utility
import utility_final

routes = [[0, 9, 4, 40, 26, 22, 125],
[0, 11, 28, 94, 93, 92, 125],
[0, 16, 7, 47, 44, 125],
[0, 17, 56, 71, 70, 65, 69, 125],
[0, 21, 121, 125],
[0, 24, 81, 80, 79, 50, 125],
[0, 25, 98, 125],
[0, 32, 107, 125],
[0, 35, 33, 6, 68, 67, 125],
[0, 36, 18, 15, 125],
[0, 37, 108, 125],
[0, 41, 113, 125],
[0, 43, 86, 2, 88, 12, 51, 125],
[0, 54, 53, 29, 52, 39, 30, 125],
[0, 58, 49, 1, 48, 10, 62, 63, 125],
[0, 64, 120, 125],
[0, 72, 27, 8, 57, 125],
[0, 74, 13, 20, 73, 42, 14, 125],
[0, 76, 99, 125],
[0, 78, 77, 34, 5, 125],
[0, 85, 84, 83, 23, 75, 125],
[0, 91, 90, 89, 66, 61, 60, 3, 45, 46, 125],
[0, 95, 102, 125],
[0, 97, 96, 125],
[0, 100, 82, 125],
[0, 101, 125],
[0, 103, 19, 125],
[0, 104, 125],
[0, 105, 125],
[0, 106, 125],
[0, 109, 125],
[0, 110, 31, 125],
[0, 111, 125],
[0, 112, 125],
[0, 114, 125],
[0, 115, 59, 125],
[0, 116, 38, 125],
[0, 117, 125],
[0, 118, 125],
[0, 119, 125],
[0, 122, 55, 125],
[0, 123, 87, 125],
[0, 124, 125],
]


locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"]
             != "Pick-up"]  # 125 locations
N_LOCS = len(locations) + 1
demands = utility_final.get_demands(N_LOCS)
utility_final.print_routes(routes, demands)

for route in routes:
    route = [str(locations[r % 125]["loc_id"]) for r in route]
    route[0] = "Depot"
    route[-1] = "Depot"
    print(" -> ".join(route))

fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)
route_groups = list(utility.split(routes, 4))

for plot_i, routes in enumerate(route_groups):
    for route in routes:
        route[-1] = 0
        xs = [locations[i]["long"] for i in route]
        ys = [locations[i]["lat"] for i in route]
        axs[plot_i % 2, plot_i // 2].plot(xs, ys)
#plt.axis('equal')
#plt.show()



for route in routes:
    if len(route) >= 6 + 2:
        route[-1] = 0
        xs = [locations[i]["long"] for i in route]
        ys = [locations[i]["lat"] for i in route]
        plt.plot(xs, ys)
plt.axis('equal')
plt.show()


for ci, route in enumerate(routes):
    for i, j in zip(route[:-1], route[1:]):
        i = i if i != D else 0
        j = j if j != D else 0
        xs = (locations[i]["long"], locations[j]["long"])
        ys = (locations[i]["lat"], locations[j]["lat"])
        plt.plot(xs, ys, c=ci, cmap="rainbow")
    color_i = (color_i + 1) % len(color_cycle)


plt.axis('equal')
plt.legend()
plt.show()
