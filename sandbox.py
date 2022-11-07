import os, json
import gurobipy as gp
import matplotlib.pyplot as plt
from gurobipy import GRB
from gurobipy import quicksum
import utility

locations = json.load(open(os.path.abspath("./data/locations.json"), "r"))
locations = [loc for loc in locations if loc["type"]
             != "Pick-up"]  # 125 locations
#subsets = utility.get_subsets2(locations, 4)
subsets = utility.get_kmeans(locations)
pass