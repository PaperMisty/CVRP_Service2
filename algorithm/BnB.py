from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from algorithm.calcDist import calculate_distance_matrix
import pandas as pd

data = pd.read_excel("web_app/static/download/location_中百仓储_武汉市.xlsx")
dist_matrix = calculate_distance_matrix(data)
print("距离矩阵:")
print(dist_matrix)
# dist_matrix = [
#   [0, 10, 15, 20],
#   [10, 0, 35, 25],
#   [15, 35, 0, 30],
#   [20, 25, 30, 0]
# ]
num_vehicles = 1
depot = 0  # 仓库节点（起点/终点）

# 建立 index 管理器
manager = pywrapcp.RoutingIndexManager(len(dist_matrix), num_vehicles, depot)

# 建立模型
routing = pywrapcp.RoutingModel(manager)

# 回调函数（这里 numpy 也能直接用）
def distance_callback(from_index, to_index):
    return int(dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# 搜索参数
search_params = pywrapcp.DefaultRoutingSearchParameters()
search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
search_params.time_limit.seconds = 5

# 求解
solution = routing.SolveWithParameters(search_params)

# 输出解
if solution:
    index = routing.Start(0)
    route = []
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))
    print("最佳路线:", route)