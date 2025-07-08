# 导入必要的库
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from .calcDist import calculate_distance_matrix
from .drawFigure import draw_figure


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
        # NNH生成的路径已经是子路径，但为了与IC兼容，我们需要将它们合并成一个单一的路径列表
        single_path = []
        if self.routes:
            single_path = [0]
            for route in self.routes:
                # 移除每个子路径的起始和结束的0点，然后连接
                single_path.extend(route[1:-1])
            single_path.append(0)

        for i in range(len(single_path) - 1):
            distance += self.distance_matrix[single_path[i]][single_path[i + 1]]
        
        return single_path, distance, self.distance_matrix
            

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
    nnh.solve()
    draw_figure(data, nnh.routes, nnh.figure_title)
    # 改良圈算法
"""    ic = IC.IC(nnh.distance_matrix, nnh.routes)
    ic.split_path()
    ic.improve()
    draw_figure(data, ic.child_paths, "武汉中百仓储超市物流配送方案-NNH-IC")"""
