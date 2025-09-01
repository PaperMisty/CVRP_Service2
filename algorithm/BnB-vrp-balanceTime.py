import time
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from calcDist import calculate_distance_matrix
import drawFigure
import pandas as pd
# === 新增: 依赖 ===
import numpy as np
import math

# -----------------------------
# 1. 数据定义
# -----------------------------
# 距离矩阵（对称）
data = pd.read_excel("location_中百仓储_武汉市.xlsx")
dist_matrix = calculate_distance_matrix(data)

# 客户需求量
demands = data["demand"] * 100  # depot 的需求为 0

# 车辆容量
vehicle_capacities = [2000] * 4
num_vehicles = len(vehicle_capacities)

# 仓库节点
depot = 0

# -----------------------------
# 2. 建立 Routing Model
# -----------------------------
manager = pywrapcp.RoutingIndexManager(len(dist_matrix), num_vehicles, depot)
routing = pywrapcp.RoutingModel(manager)

MAIN_COEF = 1000000  # 主目标的权重
COMPOSIT_SPAN_COEF = 1  # 次目标的权重
TIME_LIMIT = 30  # 求解时间限制（秒）   

# 定义距离回调函数（弧成本）
def distance_callback(from_index, to_index):
    return int(MAIN_COEF*dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

transit_callback_index = routing.RegisterTransitCallback(distance_callback)

# 定义主目标：距离之和
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# 定义副目标：minmax化 距离。
routing.AddDimension(
    transit_callback_index,
    0,                # slack
    10**12,           # 上限给很大
    True,             # start cumul to zero
    "TimeBalance"
)
timebalance_dim = routing.GetDimensionOrDie("TimeBalance")

# 设置副目标系数
timebalance_dim.SetGlobalSpanCostCoefficient(COMPOSIT_SPAN_COEF)  

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
search_params.time_limit.seconds = TIME_LIMIT

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
composite_vals = []  # 移到循环外
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

        # === 新增: 读取联合指标（Composite）的终值 ===
        end_index = routing.End(vehicle_id)
        composite_val = solution.Value(composite_dim.CumulVar(end_index))/COMPOSIT_SPAN_COEF
        composite_vals.append(composite_val)  # 这里收集所有车辆的 composite

        routes.append(route)
    
        print(
            f"Vehicle {vehicle_id} route: {route} \n "
            f"          distance (arc sum): {route_distance/MAIN_COEF} \n "
            f"          composite(end): {composite_val}"
            )
    print(f"Total distance of all routes: {total_distance/MAIN_COEF}")
    print(f"Composite values (std): {np.std(composite_vals):.1f}")
else:
    print("No solution found!")

# -----------------------------
# 7. 输出图表
# -----------------------------
if solution:
    drawFigure.draw_figure(data, routes, demands, "VRP with VisitCount Balancing")
