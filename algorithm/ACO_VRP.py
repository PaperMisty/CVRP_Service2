# 导入必要的库
import numpy as np
import time
from algorithm import IC
from algorithm.calcDist import calculate_distance_matrix

class CVRP_ACO:
    def __init__(self, data, num_ants, num_iterations, alpha, beta, rho, capacity, distance_type='haversine', figure_title="Accelerated ACO"):
        self.data = data
        self.num_ants = int(num_ants)
        self.num_iterations = int(num_iterations)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.rho = float(rho)
        self.capacity = float(capacity)
        self.distance_type = distance_type
        self.figure_title = figure_title
        
        self.num_customers = len(data)
        self.distance_matrix = calculate_distance_matrix(self.data, self.distance_type)
        # 启发信息矩阵，即距离的倒数
        self.heuristic_matrix = 1.0 / (self.distance_matrix + 1e-10) # 避免除以零
        self.pheromone = np.ones((self.num_customers, self.num_customers))
        
        self.best_path = None
        self.best_distance = float('inf')

    def run(self):
        for _ in range(self.num_iterations):
            # 为所有蚂蚁初始化路径
            all_paths = np.zeros((self.num_ants, self.num_customers), dtype=int)
            all_distances = np.zeros(self.num_ants)
            
            for ant in range(self.num_ants):
                unvisited = np.ones(self.num_customers, dtype=bool)
                unvisited[0] = False # 仓库已被访问
                
                path = [0]
                current_capacity = self.capacity
                current_city = 0
                
                while np.any(unvisited):
                    # 找出所有可访问的城市（容量允许）
                    possible_cities_mask = (self.data['demand'].values <= current_capacity) & unvisited
                    
                    # 如果没有城市可以访问，则返回仓库
                    if not np.any(possible_cities_mask):
                        path.append(0)
                        current_city = 0
                        current_capacity = self.capacity
                        continue

                    possible_indices = np.where(possible_cities_mask)[0]
                    
                    # 计算转移概率（向量化）
                    pheromone_slice = self.pheromone[current_city, possible_indices]
                    heuristic_slice = self.heuristic_matrix[current_city, possible_indices]
                    
                    probabilities = (pheromone_slice ** self.alpha) * (heuristic_slice ** self.beta)
                    prob_sum = np.sum(probabilities)
                    
                    if prob_sum == 0: # 如果概率和为0，则随机选择一个
                        next_city = np.random.choice(possible_indices)
                    else:
                        probabilities /= prob_sum
                        next_city = np.random.choice(possible_indices, p=probabilities)

                    # 更新路径和状态
                    path.append(next_city)
                    all_distances[ant] += self.distance_matrix[current_city, next_city]
                    current_capacity -= self.data['demand'][next_city]
                    unvisited[next_city] = False
                    current_city = next_city

                # 完成路径，返回仓库
                all_distances[ant] += self.distance_matrix[current_city, 0]
                path.append(0)

                # 更新全局最优解
                if all_distances[ant] < self.best_distance:
                    self.best_distance = all_distances[ant]
                    self.best_path = path

            # 更新信息素（向量化）
            self.pheromone *= (1 - self.rho) # 信息素挥发
            if self.best_path:
                for i in range(len(self.best_path) - 1):
                    start, end = self.best_path[i], self.best_path[i+1]
                    # 仅为最优路径增加信息素（精英蚂蚁策略）
                    self.pheromone[start, end] += 1.0 / self.best_distance
                    self.pheromone[end, start] = self.pheromone[start, end] # 对称矩阵

        return self.best_path, self.best_distance, self.distance_matrix

if __name__ == "__main__":
    # 示例用法
    data_dict = {
        'longitude': np.random.rand(20) * 100,
        'latitude': np.random.rand(20) * 100,
        'demand': np.random.randint(1, 10, 20)
    }
    import pandas as pd
    data = pd.DataFrame(data_dict)
    data.iloc[0]['demand'] = 0 # 仓库需求为0

    start_time = time.time()
    aco = CVRP_ACO(data=data, num_ants=20, num_iterations=100, alpha=1.0, beta=5.0, rho=0.5, capacity=50)
    best_path, best_distance, distance_matrix = aco.run()
    end_time = time.time()

    print(f"Accelerated ACO finished in {end_time - start_time:.2f}s")
    print("Best distance:", best_distance)
    
    # 使用IC进行改进
    if best_path:
        ic_solver = IC.IC(distance_matrix, best_path)
        ic_solver.split_path()
        child_paths, improved_distance = ic_solver.improve()
        print("Improved distance with IC:", improved_distance)
        print("Routes:", child_paths)
