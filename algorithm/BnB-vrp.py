import time
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from algorithm.calcDist import calculate_distance_matrix
from algorithm import drawFigure
import pandas as pd
# -----------------------------
# 1. 数据定义
# -----------------------------
# 距离矩阵（对称）
data = pd.read_excel("web_app/static/download/location_中百仓储_武汉市.xlsx")
dist_matrix = calculate_distance_matrix(data)

# 客户需求量
demands = data["demand"]*100  # depot 的需求为 0

# 车辆容量
vehicle_capacities = [2000]*4
num_vehicles = len(vehicle_capacities)

# 仓库节点
depot = 0

# -----------------------------
# 2. 建立 Routing Model
# -----------------------------
manager = pywrapcp.RoutingIndexManager(len(dist_matrix), num_vehicles, depot)
routing = pywrapcp.RoutingModel(manager)

# 距离回调函数
def distance_callback(from_index, to_index):
    return int(dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# -----------------------------
# 3. 容量约束
# -----------------------------
def demand_callback(from_index):
    return int(demands[manager.IndexToNode(from_index)])

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # slack
    vehicle_capacities,  # 每辆车的容量
    True,  # start cumul to zero
    'Capacity'
)

# -----------------------------
# 4. 搜索参数
# -----------------------------
search_params = pywrapcp.DefaultRoutingSearchParameters()
search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
search_params.time_limit.seconds = 30

# -----------------------------
# 5. 求解
# -----------------------------
a = time.time()
solution = routing.SolveWithParameters(search_params)
b = time.time()
print("求解时间：", b - a)

# -----------------------------
# 6. 输出路线和长度
# -----------------------------
routes = []
if solution:
    total_distance = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_demand = 0
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_demand += demands[manager.IndexToNode(previous_index)]
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route.append(manager.IndexToNode(index))
        total_distance += route_distance
        
        print(f"Vehicle {vehicle_id} route: {route} | distance: {route_distance} | demand: {route_demand}")
        routes.append(route)
    print(f"Total distance of all routes: {total_distance}")
else:
    print("No solution found!")

# -----------------------------
# 7. 输出图表
# -----------------------------
if solution:
    drawFigure.draw_figure(data, routes, demands, "Branch and Bound VRP Solution")