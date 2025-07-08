# 导入必要的库
import numpy as np
import time
from algorithm import IC
from algorithm.calcDist import calculate_distance_matrix

class CVRP_GA:
    def __init__(self, data, population, num_generations, mutation_rate, crossover_rate, capacity, **kwargs):
        self.data = data
        self.population_size = int(population)
        self.num_generations = int(num_generations)
        self.mutation_rate = float(mutation_rate)
        self.crossover_rate = float(crossover_rate)
        self.capacity = float(capacity)
        
        self.num_customers = len(data)
        self.customer_indices = np.arange(1, self.num_customers)
        self.demands = self.data['demand'].values
        self.distance_matrix = calculate_distance_matrix(self.data)
        
        self.population = self._initialize_population()
        self.best_path = None
        self.best_distance = float('inf')

    def _initialize_population(self):
        """初始化种群，每个个体是一个客户点的随机排列"""
        population = np.zeros((self.population_size, self.num_customers - 1), dtype=int)
        for i in range(self.population_size):
            population[i] = np.random.permutation(self.customer_indices)
        return population

    def _calculate_fitness(self):
        """计算整个种群的适应度（向量化）"""
        all_distances = np.zeros(self.population_size)
        for i, individual in enumerate(self.population):
            path = [0]
            current_capacity = self.capacity
            # 遍历基因序列（客户点排列）
            for customer_idx in individual:
                if current_capacity < self.demands[customer_idx]:
                    # 容量不足，返回仓库
                    path.append(0)
                    current_capacity = self.capacity
                path.append(customer_idx)
                current_capacity -= self.demands[customer_idx]
            path.append(0) # 结束时返回仓库
            
            # 计算总距离
            dist = 0
            for j in range(len(path) - 1):
                dist += self.distance_matrix[path[j], path[j+1]]
            all_distances[i] = dist
        
        # 更新全局最优解
        min_dist_idx = np.argmin(all_distances)
        if all_distances[min_dist_idx] < self.best_distance:
            self.best_distance = all_distances[min_dist_idx]
            # 重新生成最优路径以保存
            best_individual = self.population[min_dist_idx]
            best_path_full = [0]
            cap = self.capacity
            for cust in best_individual:
                if cap < self.demands[cust]:
                    best_path_full.append(0)
                    cap = self.capacity
                best_path_full.append(cust)
                cap -= self.demands[cust]
            best_path_full.append(0)
            self.best_path = best_path_full

        # 适应度是距离的倒数，避免除以零
        return 1.0 / (all_distances + 1e-10)

    def _selection(self, fitness):
        """轮盘赌选择"""
        fitness_sum = np.sum(fitness)
        if fitness_sum == 0: # 避免除以零
            # 如果所有适应度都为0，则随机选择
            indices = np.random.choice(self.population_size, size=self.population_size, replace=True)
        else:
            probabilities = fitness / fitness_sum
            indices = np.random.choice(self.population_size, size=self.population_size, replace=True, p=probabilities)
        self.population = self.population[indices]

    def _crossover(self):
        """顺序交叉 (Order Crossover, OX1)"""
        for i in range(0, self.population_size, 2):
            if np.random.rand() < self.crossover_rate:
                parent1, parent2 = self.population[i], self.population[i+1]
                
                start, end = sorted(np.random.choice(range(self.num_customers - 1), 2, replace=False))
                
                # 创建子代
                offspring1 = -np.ones_like(parent1)
                offspring2 = -np.ones_like(parent2)
                
                # 复制交叉段
                offspring1[start:end+1] = parent1[start:end+1]
                offspring2[start:end+1] = parent2[start:end+1]
                
                # 填充剩余部分
                p2_filtered = [item for item in parent2 if item not in offspring1]
                p1_filtered = [item for item in parent1 if item not in offspring2]
                
                offspring1[offspring1 == -1] = p2_filtered
                offspring2[offspring2 == -1] = p1_filtered
                
                self.population[i], self.population[i+1] = offspring1, offspring2

    def _mutation(self):
        """交换变异"""
        for i in range(self.population_size):
            if np.random.rand() < self.mutation_rate:
                individual = self.population[i]
                idx1, idx2 = np.random.choice(range(self.num_customers - 1), 2, replace=False)
                individual[idx1], individual[idx2] = individual[idx2], individual[idx1]

    def run(self):
        for _ in range(self.num_generations):
            fitness = self._calculate_fitness()
            self._selection(fitness)
            self._crossover()
            self._mutation()
        
        # 最后一次计算以确保best_path是最新且正确的
        self._calculate_fitness()
        
        return self.best_path, self.best_distance, self.distance_matrix

if __name__ == "__main__":
    data_dict = {
        'longitude': np.random.rand(20) * 100,
        'latitude': np.random.rand(20) * 100,
        'demand': np.random.randint(1, 10, 20)
    }
    import pandas as pd
    data = pd.DataFrame(data_dict)
    data.iloc[0]['demand'] = 0

    start_time = time.time()
    ga = CVRP_GA(data=data, population=50, num_generations=200, mutation_rate=0.1, crossover_rate=0.8, capacity=50)
    best_path, best_distance, distance_matrix = ga.run()
    end_time = time.time()

    print(f"Accelerated GA finished in {end_time - start_time:.2f}s")
    print("Best distance:", best_distance)

    if best_path:
        ic_solver = IC.IC(distance_matrix, best_path)
        ic_solver.split_path()
        child_paths, improved_distance = ic_solver.improve()
        print("Improved distance with IC:", improved_distance)
        print("Routes:", child_paths)
