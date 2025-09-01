# 导入必要的库
import numpy as np
import pandas as pd
import time
from algorithm import IC
from algorithm.calcDist import calculate_distance_matrix
from algorithm.drawFigure import draw_figure

class CVRP_CW:
    def __init__(self, data, capacity, distance_type='haversine', figure_title="武汉中百仓储超市物流配送方案-CW"):
        """
        初始化CW类
        :param data: 包含客户点信息的DataFrame
        :param capacity: 车辆容量约束
        :param distance_type: 距离类型，默认为'haversine'
        :param figure_title: 图像标题，默认为'武汉中百仓储超市物流配送方案-CW'
        """
        self.data = data
        self.capacity = capacity
        self.distance_type = distance_type
        self.figure_title = figure_title
        self.distance_matrix = None
        self.savings = None
        self.routes = []
        self.best_distance = float('inf')

    def calculate_savings(self):
        """计算节约值矩阵"""
        n = len(self.data)
        self.savings = np.zeros((n, n))
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    # 节约值 = d0i + d0j - dij
                    self.savings[i][j] = (self.distance_matrix[0][i] + 
                                        self.distance_matrix[0][j] - 
                                        self.distance_matrix[i][j])
        # 保存节约值矩阵
        print(self.savings)
        index_labels = list(range(0, len(self.savings)))
        # 使用 pandas.DataFrame() 的 index 和 columns 参数直接指定索引
        self.savings = pd.DataFrame(self.savings,index=index_labels,columns=index_labels)

        self.savings.to_excel('output/savings_matrix.xlsx')
    def is_feasible(self, route, i, j):
        """检查合并路径是否满足容量约束"""
        total_demand = 0
        for node in route:
            if node != 0:
                total_demand += self.data["demand"][node]
        if i not in route:
            total_demand += self.data["demand"][i]
        if j not in route:
            total_demand += self.data["demand"][j]
        return total_demand <= self.capacity

    def merge_routes(self, route1, route2, i, j):
        """
        合并两条路径，连接i和j
        :param route1: 包含i的路径
        :param route2: 包含j的路径
        :param i: 正在考虑连接的客户点i
        :param j: 正在考虑连接的客户点j
        """
        # 确定i在route1中的位置 (第二个元素或倒数第二个元素)
        i_is_start_of_route1 = (route1[1] == i)
        i_is_end_of_route1 = (route1[-2] == i)

        # 确定j在route2中的位置 (第二个元素或倒数第二个元素)
        j_is_start_of_route2 = (route2[1] == j)
        j_is_end_of_route2 = (route2[-2] == j)

        merged_route = None

        # 情况1: route1以i结尾，route2以j开头
        # [0, ..., i, 0] + [0, j, ...] -> [0, ..., i, j, ...]
        if i_is_end_of_route1 and j_is_start_of_route2:
            merged_route = route1[:-1] + route2[1:]
        # 情况2: route1以i开头，route2以j开头
        # [0, i, ..., 0] + [0, j, ...] -> [0, ..., i, j, ...] (route1反转)
        elif i_is_start_of_route1 and j_is_start_of_route2:
            merged_route = route1[::-1][:-1] + route2[1:]
        # 情况3: route1以i结尾，route2以j结尾
        # [0, ..., i, 0] + [0, ..., j, 0] -> [0, ..., i, j, ..., 0] (route2反转)
        elif i_is_end_of_route1 and j_is_end_of_route2:
            merged_route = route1[:-1] + route2[::-1][1:]
        # 情况4: route1以i开头，route2以j结尾
        # [0, i, ..., 0] + [0, ..., j, 0] -> [0, ..., i, j, ..., 0] (route1反转, route2反转)
        elif i_is_start_of_route1 and j_is_end_of_route2:
            merged_route = route1[::-1][:-1] + route2[::-1][1:]

        # 确保合并后的路径以配送中心(0)开头和结尾
        if merged_route and merged_route[0] == 0 and merged_route[-1] == 0:
            return merged_route
        return None

    def calculate_route_distance(self, route):
        """计算路径总距离"""
        distance = 0
        for i in range(len(route)-1):
            distance += self.distance_matrix[route[i]][route[i+1]]
        return distance

    def run(self):
        """运行CW算法"""
        # 计算距离矩阵
        self.distance_matrix = calculate_distance_matrix(self.data, self.distance_type)
        
        # 计算节约值矩阵
        self.calculate_savings()
        
        # 初始化路径(每个客户一条路径)
        n = len(self.data)
        self.routes = [[0, i, 0] for i in range(1, n)]
        
        # 按节约值从大到小排序
        savings_list = []
        for i in range(1, n):
            for j in range(i+1, n):
                savings_list.append((i, j, self.savings[i][j]))
        savings_list.sort(key=lambda x: x[2], reverse=True)
        
        # 主循环
        for i, j, saving in savings_list:
            # 找到包含i和j的路径
            route_i = None
            route_j = None
            route_i_idx = -1
            route_j_idx = -1
            
            for idx, route in enumerate(self.routes):
                if i in route:
                    route_i = route
                    route_i_idx = idx
                if j in route:
                    route_j = route
                    route_j_idx = idx
                    
            # 如果i和j在不同路径中
            if (route_i is not None and route_j is not None and 
                route_i != route_j and 
                (i == route_i[1] or i == route_i[-2]) and
                (j == route_j[1] or j == route_j[-2])):
                
                # 尝试合并路径
                merged_route = self.merge_routes(route_i, route_j, i, j)
                if merged_route and self.is_feasible(merged_route, i, j):
                    self.routes.pop(max(route_i_idx, route_j_idx))
                    self.routes.pop(min(route_i_idx, route_j_idx))
                    self.routes.append(merged_route)
        
        # 计算总距离
        total_distance = sum(self.calculate_route_distance(route) for route in self.routes)
        self.best_distance = total_distance
        
        # 将所有路径合并为一条路径(为了与其他算法格式统一)
        best_path = []
        for route in self.routes:
            best_path.extend(route[:-1])
        best_path.append(0)
        
        return best_path, self.best_distance, self.distance_matrix

if __name__ == "__main__":
    a = time.time()
    # 读取数据
    data = pd.read_excel('web_app/static/download/location_中百仓储_武汉市.xlsx')
    data["longitude"] = data["longitude"].astype(float)
    data["latitude"] = data["latitude"].astype(float)
    data["demand"] = data["demand"].astype(float)

    cw = CVRP_CW(data=data, capacity=20)
    best_path, best_distance, distance_matrix = cw.run()

    ic = IC.IC(distance_matrix, best_path)
    ic.split_path()
    child_paths, best_distance = ic.improve()
    print("CW-IC最短距离：", best_distance)
    print("CW-IC最短路径：", child_paths)
    b = time.time()
    print("运行时间：", b-a)

    draw_figure(data, child_paths, demands=data["demand"], figure_title="CW-IC")
