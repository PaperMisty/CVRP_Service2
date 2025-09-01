# -- coding utf-8 --
# author: PaperMisty & ChatGPT
# improve circle algorithm，用于优化最终路径的小trick
class IC():
    def __init__(self: object, distance_matrix: list[list[float]], child_paths: list[list[int]]):
        self.distance_matrix = distance_matrix
        self.child_paths = child_paths
        
    # 计算总距离
    def calc_total_distance(self):
        self.best_distance = 0
        for child_path in self.child_paths:
            for i in range(len(child_path) - 1):
                self.best_distance += self.distance_matrix[child_path[i]][child_path[i + 1]]
        return self.best_distance
    # 改善路线
    def improve(self):
        # 测试原路径长度
        original_distance = self.calc_total_distance()
        print("original length:", original_distance)
        # 对每条路径进行改进。修改 child_path 会影响到 self.child_paths，因为 child_path 是 self.child_paths 中的一个引用。
        for child_path in self.child_paths:
            improved = True
            while improved:
                improved = False
                for i in range(len(child_path) - 3):
                    for j in range(i + 2, len(child_path) - 1):
                        # 2-opt改进
                        if (self.distance_matrix[child_path[i]][child_path[i+1]] + 
                            self.distance_matrix[child_path[j]][child_path[j+1]] > 
                            self.distance_matrix[child_path[i]][child_path[j]] + 
                            self.distance_matrix[child_path[i+1]][child_path[j+1]]):
                            
                            # 交换节点
                            child_path[i+1], child_path[j] = child_path[j], child_path[i+1]
                            improved = True
        # 改善路径长度
        improved_distance = self.calc_total_distance()
        print("improved length:", improved_distance)
        return self.child_paths, improved_distance

        