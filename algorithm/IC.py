import numpy as np
import matplotlib.pyplot as plt
# improve circle algorithm
class IC():
    def __init__(self, distance_matrix, best_path=None):
        self.distance_matrix = distance_matrix
        self.best_path = best_path
        self.child_paths = []  # 每次初始化时清空子路径
        self.best_distance = 0
        
    # split self.best_path by 0
    def split_path(self):
        # 清空之前的路径
        self.child_paths = []
        
        if not self.best_path:
            return
            
        start = 0
        for i in range(len(self.best_path)):
            if self.best_path[i] == 0:
                if i != start:
                    self.child_paths.append(self.best_path[start:i + 1])
                    start = i
    
    def improve(self):
        # 确保路径已经分割
        if not self.child_paths:
            self.split_path()
            
        # 对每条路径进行改进
        for path in self.child_paths:
            improved = True
            while improved:
                improved = False
                for i in range(len(path) - 3):
                    for j in range(i + 2, len(path) - 1):
                        # 2-opt改进
                        if (self.distance_matrix[path[i]][path[i+1]] + 
                            self.distance_matrix[path[j]][path[j+1]] > 
                            self.distance_matrix[path[i]][path[j]] + 
                            self.distance_matrix[path[i+1]][path[j+1]]):
                            
                            # 交换节点
                            path[i+1], path[j] = path[j], path[i+1]
                            improved = True

        # 计算总距离
        total_distance = 0
        for path in self.child_paths:
            for i in range(len(path) - 1):
                total_distance += self.distance_matrix[path[i]][path[i + 1]]
        
        self.best_distance = total_distance
        
        # 返回去掉仓库点的路径（只保留客户点）
        customer_paths = []
        for path in self.child_paths:
            # 去掉路径中的仓库点（0）
            customer_path = [node for node in path if node != 0]
            if customer_path:  # 只添加非空路径
                customer_paths.append(customer_path)
        
        return customer_paths, self.best_distance