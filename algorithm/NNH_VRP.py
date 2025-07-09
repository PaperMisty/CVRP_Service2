# 导入必要的库
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from .calcDist import calculate_distance_matrix
from .drawFigure import draw_figure
from . import IC


# 最近邻启发式算法(NNH)求解带约束的车辆路径问题(CVRP)
class CVRP_NNH:
    def __init__(self, data, vehicle_capacity, distance_type='haversine', figure_title = "武汉中百仓储超市物流配送方案-NNH"):
        """
        初始化CVRP_NNH类
        :param data: 包含客户点信息的DataFrame
        :param vehicle_capacity: 车辆容量约束
        :param distance_type: 距离类型，默认为'haversine'
        :param figure_title: 图像标题，默认为'武汉中百仓储超市物流配送方案-NNH'
        """
        self.data = data
        self.demands = data["demand"]  # 客户需求量
        self.vehicle_capacity = vehicle_capacity  # 车辆容量
        self.num_customers = len(data)  # 客户数量
        self.distance_type = distance_type # 距离类型
        self.figure_title = figure_title # 图像标题

    def find_nearest_neighbor(self, current_location, unvisited):
        """
        寻找距离当前位置最近的未访问客户点
        :param current_location: 当前位置
        :param unvisited: 未访问的客户点集合
        :return: 最近的客户点编号
        """
        nearest = None
        min_distance = float('inf')
        for customer in unvisited:
            if self.distance_matrix[current_location][customer] < min_distance:
                nearest = customer
                min_distance = self.distance_matrix[current_location][customer]
        return nearest

    def solve(self):
        """
        求解CVRP问题
        """
        self.distance_matrix = calculate_distance_matrix(self.data, self.distance_type)
        self.routes = []  # 存储所有路径
        unvisited = set(range(1, self.num_customers))  # 未访问客户点集合，0为配送中心

        # 当还有未访问的客户点时继续循环
        while unvisited:
            self.route = [0]  # 当前路径从配送中心开始
            capacity_remaining = self.vehicle_capacity  # 剩余车辆容量
            while unvisited:
                current_location = self.route[-1]
                nearest = self.find_nearest_neighbor(current_location, unvisited)
                # 如果没有找到最近点或超出容量约束，结束当前路径
                if nearest is None or self.demands[nearest] > capacity_remaining:
                    break
                self.route.append(nearest)
                unvisited.remove(nearest)
                capacity_remaining -= self.demands[nearest]
            self.route.append(0)  # 返回配送中心
            self.routes.append(self.route)
        
        # 计算总距离
        distance = 0
        
        # 为了与IC兼容，需要将路径转换为正确的格式
        # IC期望的格式是一个包含所有节点的单一路径，用0分隔不同车辆的路径
        best_path = []
        if self.routes:
            # 第一条路径直接添加
            best_path.extend(self.routes[0])
            # 后续路径去掉开头的0（因为前一条路径已经以0结尾）
            for route in self.routes[1:]:
                best_path.extend(route[1:])
        
        # 计算总距离
        for i in range(len(best_path) - 1):
            distance += self.distance_matrix[best_path[i]][best_path[i + 1]]
        
        return best_path, distance, self.distance_matrix
    
    def solve_with_ic(self):
        """
        求解CVRP问题并使用IC进行路径优化
        """
        # 首先运行基本的NNH算法
        best_path, distance, distance_matrix = self.solve()
        
        # 使用IC进行路径改进
        ic = IC.IC(distance_matrix, best_path)
        improved_routes, improved_distance = ic.improve()
        
        print(f"NNH原始距离: {distance}")
        print(f"NNH-IC改进距离: {improved_distance}")
        print(f"改进幅度: {((distance - improved_distance) / distance * 100):.2f}%")
        
        # 返回改进后的路径和距离
        return improved_routes, improved_distance, distance_matrix
            

# 主程序
if __name__ == '__main__':
    # 读取数据
    data = pd.read_excel("./data/location_中百仓储_武汉市.xlsx")
    # 转换数据类型
    data["longitude"] = data["longitude"].astype(float)
    data["latitude"] = data["latitude"].astype(float)
    data["demand"] = data["demand"].astype(float)
    
    # 创建CVRP_NNH实例并求解
    nnh = CVRP_NNH(data, 4)
    
    # 不使用IC的原始解
    best_path, distance, distance_matrix = nnh.solve()
    print("NNH原始路径:", nnh.routes)
    print("NNH原始距离:", distance)
    draw_figure(data, nnh.routes, nnh.figure_title)
    
    # 使用IC改进的解
    improved_routes, improved_distance, _ = nnh.solve_with_ic()
    print("NNH-IC改进路径:", improved_routes)
    print("NNH-IC改进距离:", improved_distance)
    draw_figure(data, improved_routes, "武汉中百仓储超市物流配送方案-NNH-IC")