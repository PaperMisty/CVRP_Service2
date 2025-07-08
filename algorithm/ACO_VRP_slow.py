# 导入必要的库
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
from . import IC

from .calcDist import calculate_distance_matrix
from .drawFigure import draw_figure

# ACO算法
class CVRP_ACO:
  def __init__(self, data, num_ants, num_iterations, alpha, beta, rho, capacity, distance_type='haversine', figure_title="武汉中百仓储超市物流配送方案-ACO（2024/12/15，xhs演示）"):
    """
    初始化ACO类
    :param data: 包含客户点信息的DataFrame
    :param num_ants: 蚂蚁数量
    :param num_iterations: 迭代次数
    :param alpha: 信息素重要程度因子
    :param beta: 启发函数重要程度因子
    :param rho: 信息素挥发因子
    :param capacity: 车辆容量约束
    :param distance_type: 距离类型，默认为'haversine'
    :param figure_title: 图像标题，默认为'武汉中百仓储超市物流配送方案-ACO'
    """
    self.data = data
    self.num_ants = num_ants
    self.num_iterations = num_iterations
    self.alpha = alpha
    self.beta = beta
    self.rho = rho
    self.pheromone = np.ones((len(data),len(data)))
    self.distance_matrix = None
    self.capacity = capacity
    self.best_path = None
    self.best_distance = float('inf')
    self.distance_type = distance_type
    self.figure_title = figure_title

  # 计算到下一个节点概率
  # 概率 = 信息素启发 * 能见度启发
  def calculate_probabilities(self, current_city, unvisited_cities):
    self.probabilities = []
    for city in unvisited_cities:
      self.probabilities.append(self.pheromone[current_city][city] ** self.alpha * (1.0 / self.distance_matrix[current_city][city]) ** self.beta)
    self.probabilities /= np.sum(self.probabilities)
    
  # 更新信息素
  def update_pheromone(self, path):
    for i in range(len(path) - 1):
      # ant quantity system
      # 某确切路径组，i->j信息素 = 未挥发信息素 + 补充上 1/距离
      delta_pheromone  = 1 / self.distance_matrix[path[i]][path[i + 1]]
      self.pheromone[path[i]][path[i + 1]] = (1 - self.rho) * self.pheromone[path[i]][path[i + 1]] + self.rho * delta_pheromone

  # 绘制收敛曲线
  def plot_convergence_curve(self):
    plt.figure(figsize=(10, 10))
    plt.title("武汉中百仓储超市配送优化收敛曲线", fontsize=20)
    plt.plot(self.ant_best_individual_distance, label = "ACO")
    plt.show()

  # 运行ACO算法
  def run(self):
    self.distance_matrix = calculate_distance_matrix(self.data, self.distance_type)
    # 记录每一代所有蚂蚁的路径
    self.ant_paths = []
    # 记录每一代最短距离
    self.ant_best_individual_distance = []
    for _ in range(self.num_iterations):
      # 每一代蚂蚁的路径
      for ant in range(self.num_ants):
        unvisited_cities = list(range(1, len(self.data)))
        path = [0]
        distance = 0
        capacity = self.capacity

        while unvisited_cities:
          #两种情况回仓，一是车厢货量不足，二是所有点配送结束
          temp_unvisited_cities = unvisited_cities.copy()
        
          # tmp用来测试会不会剩余节点都不能配送（货量原因）
          tmp = temp_unvisited_cities.copy()
          # array对象的remove方法会改变for循环里面原对象
          # 观察现存货量能否满足剩余某节点
          for city in temp_unvisited_cities:
            next_city_demand = self.data["demand"][city]
            if capacity - next_city_demand < 0:
              tmp.remove(city)
          # 如果剩余节点均不能配送，即待选点为空，返回仓库
          if not tmp:
            capacity = self.capacity
            distance += self.distance_matrix[path[-1]][0]
            path.append(0)
            continue

          # 在待选点中随机选择下一个节点
          for city in temp_unvisited_cities:
            self.calculate_probabilities(path[-1], temp_unvisited_cities)
          next_city = np.random.choice(temp_unvisited_cities, p = self.probabilities)
          next_city_demand = self.data["demand"][next_city]
          
          capacity -= next_city_demand
          distance += self.distance_matrix[path[-1]][next_city]

          path.append(next_city)
          unvisited_cities.remove(next_city)
        
        # 所有节点都访问完毕，返回仓库
        distance += self.distance_matrix[path[-1]][0]
        path.append(0)

        if distance < self.best_distance:
          self.best_path = path
          self.best_distance = distance
      self.ant_paths.append(path)
      # 记录收敛曲线距离
      self.ant_best_individual_distance.append(self.best_distance)
      
      # 更新信息素
      for path in self.ant_paths:
        self.update_pheromone(path)
    # self.plot_convergence_curve()
    return self.best_path, self.best_distance, self.distance_matrix

    

if __name__ == "__main__":
  a = time.time()
  # 读取数据
  data = pd.read_excel('./data/location_中百仓储_武汉市.xlsx')
  data["longitude"] = data["longitude"].astype(float)
  data["latitude"] = data["latitude"].astype(float)
  data["demand"] = data["demand"].astype(float)

  aco = CVRP_ACO(data=data, num_ants=5, num_iterations=5, alpha=1, beta=5, rho=0.5, capacity=4)
  best_path, best_distance, distance_matrix = aco.run()
  print("ACO最短距离：", best_distance)
  print("ACO最短路径：", best_path)

  b = time.time()
  print("ACO运行时间：", b-a)

  ic = IC.IC(distance_matrix, best_path)
  ic.split_path()
  child_paths, best_distance = ic.improve()
  print("ACO-IC最短距离：", best_distance)
  print("ACO-IC最短路径：", child_paths)
  c = time.time()
  print("IC运行时间：", c-b)

  draw_figure(data, child_paths, aco.figure_title)
