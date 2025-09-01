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
# === 新增: 复合指标参数（每访问一个客户要“抵扣”的权重 λ，单位需与距离一致/同尺度） ===
LAMBDA_PER_VISIT = 10  # 举例：你可依据业务意义调整
MAIN_COEF = 1000000  # 主目标（距离）的权重
COMPOSIT_SPAN_COEF = 1  # 次目标（复合）的权重
TIME_LIMIT = 30  # 求解时间限制（秒）   

# === 新增: 选择缩放因子，确保 composite 的增量非负 ===
# 维度 transit 必须 >= 0；我们放大距离，使得 (scale*distance - lambda) >= 0
nonzero = dist_matrix[dist_matrix > 0]
min_nonzero_dist = float(np.min(nonzero)) if nonzero.size else 1.0
scale = max(1, math.ceil((LAMBDA_PER_VISIT + 1) / min_nonzero_dist))

# === 新增: 预计算缩放后的距离矩阵（用于 composite 维度） ===
scaled_dist = (dist_matrix * scale).astype(int)

# 距离回调函数（弧成本）
# === 保持原有弧成本: 仍用原始距离做“总距离最小化”的主目标 ===
def distance_callback(from_index, to_index):
    return int(MAIN_COEF*dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# === 新增: 复合维度（Composite）===
# 目标是做 max_v { sum(scaled_dist) - LAMBDA_PER_VISIT * visit_count } 的 min–max
# 实现方式：到达客户节点(to_node != depot)时“抵扣”lambda；到达 depot 不抵扣。
def composite_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    base = int(scaled_dist[from_node][to_node])
    deduct = LAMBDA_PER_VISIT if to_node != depot else 0
    val = (base - deduct)
    # 理论上 scale 已保证 >=0；为安全起见再夹一下
    return val if val >= 0 else 0

composite_cb_index = routing.RegisterTransitCallback(composite_callback)

routing.AddDimension(
    composite_cb_index,
    0,                # slack
    10**12,           # 上限给很大
    True,             # start cumul to zero
    "Composite"
)
composite_dim = routing.GetDimensionOrDie("Composite")

# === 新增: 对联合指标做 min–max（通过 span）===
# 系数越大，越强调“最差车辆的复合值”要小（即公平性越强）
composite_dim.SetGlobalSpanCostCoefficient(COMPOSIT_SPAN_COEF)  # 可调：越大越偏向公平(min–max)

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
