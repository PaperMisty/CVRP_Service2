# Let's implement a tiny Branch & Bound demo for a 4-city symmetric TSP.
# We'll show the search steps in a table so you can see where pruning happens.

from itertools import permutations
import math
import pandas as pd

# Define 4 city coordinates (chosen to make pruning visible)
coords = {
    0: (0, 0),
    1: (1, 0),
    2: (2, 0),
    3: (0, 2),
}

# Compute symmetric distance matrix (Euclidean, rounded to 2 decimals for display)
def dist(a, b):
    ax, ay = coords[a]
    bx, by = coords[b]
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

N = len(coords)
D = [[0.0]*N for _ in range(N)]
for i in range(N):
    for j in range(N):
        if i != j:
            D[i][j] = dist(i, j)

# A simple admissible lower bound:
# bound(partial path P ending at 'last', unvisited set R):
#   = cost_so_far(P)
#     + min_edge(last -> R) if R else dist(last, start)
#     + MST_cost(R)     (MST over remaining nodes only)
#     + min_edge(R -> start) if R else 0
#
# This is optimistic (admissible) but easy to compute and good enough for a demo.

def mst_cost(nodes):
    """Prim's algorithm for MST cost over 'nodes' using the distance matrix D."""
    nodes = list(nodes)
    if len(nodes) <= 1:
        return 0.0
    used = {nodes[0]}
    not_used = set(nodes[1:])
    total = 0.0
    while not_used:
        best = math.inf
        best_v = None
        for u in used:
            for v in not_used:
                if D[u][v] < best:
                    best = D[u][v]
                    best_v = v
        total += best
        used.add(best_v)
        not_used.remove(best_v)
    return total

def min_edge_from(u, candidates):
    if not candidates:
        return math.inf
    return min(D[u][v] for v in candidates)

def min_edge_to_start(candidates, start):
    if not candidates:
        return 0.0
    return min(D[v][start] for v in candidates)

# Branch & Bound search (depth-first) with logging
start = 0
best_cost = math.inf
best_tour = None
log_rows = []

def log_step(path, cost_so_far, bound_val, action, best_cost_so_far):
    log_rows.append({
        "Partial path": "->".join(map(str, path)),
        "cost_so_far": round(cost_so_far, 2),
        "bound": round(bound_val, 2) if bound_val is not None else None,
        "action": action,
        "best_cost_so_far": round(best_cost_so_far, 2) if best_cost_so_far < math.inf else None,
    })

def lower_bound(path):
    last = path[-1]
    unvisited = set(range(N)) - set(path)
    cost_so_far = sum(D[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0.0
    if not unvisited:
        # must close the tour
        return cost_so_far + D[last][start]
    # optimistic additions
    enter = min_edge_from(last, unvisited)
    tree = mst_cost(unvisited)
    exit_ = min_edge_to_start(unvisited, start)
    return cost_so_far + enter + tree + exit_

def dfs(path):
    global best_cost, best_tour
    lb = lower_bound(path)
    cost_so_far = sum(D[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0.0
    if lb >= best_cost:
        log_step(path, cost_so_far, lb, "prune", best_cost)
        return
    # If all visited, compute full tour cost
    if len(path) == N:
        total_cost = cost_so_far + D[path[-1]][start]
        if total_cost < best_cost:
            best_cost = total_cost
            best_tour = path + [start]
        log_step(path + [start], total_cost, total_cost, "complete", best_cost)
        return
    # Expand children in ascending city index order (excluding start if not first)
    unvisited = [v for v in range(N) if v not in path]
    for v in unvisited:
        if v == start:
            continue
        new_path = path + [v]
        # quick incremental check: if cost_so_far already exceeds best, we still rely on bound pruning soon
        lb_child = lower_bound(new_path)
        if lb_child >= best_cost:
            new_cost = sum(D[new_path[i]][new_path[i+1]] for i in range(len(new_path)-1))
            log_step(new_path, new_cost, lb_child, "prune", best_cost)
            continue
        # otherwise, log expansion and go deeper
        new_cost = sum(D[new_path[i]][new_path[i+1]] for i in range(len(new_path)-1))
        log_step(new_path, new_cost, lb_child, "expand", best_cost)
        dfs(new_path)

# Start search
log_step([start], 0.0, lower_bound([start]), "start", best_cost)
dfs([start])

df = pd.DataFrame(log_rows)

# # Display the step log as a table for the user
# from caas_jupyter_tools import display_dataframe_to_user
# display_dataframe_to_user("Branch & Bound demo (4-city TSP)", df)

# Also output the best tour found and its length for reference (not the main teaching focus)
print(f"Best tour found: {best_tour} (cost {best_cost})")

