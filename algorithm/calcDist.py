import numpy as np
# 欧氏距离
def euclidean_distance(x1, y1, x2, y2):
    """
    计算两点间欧氏距离
    :return: 两点间距离
    """
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) + 1e-6
# 曼哈顿距离
def manhattan_distance(x1, y1, x2, y2):
    """
    计算两点间曼哈顿距离
    :return: 两点间曼哈顿距离
    """
    return abs(x1 - x2) + abs(y1 - y2)
# 切比雪夫距离
def chebyshev_distance(x1, y1, x2, y2):
    """
    计算两点间切比雪夫距离
    :return: 两点间切比雪夫距离
    """
    return max(abs(x1 - x2), abs(y1 - y2))
# 哈弗辛距离
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    计算两点间球面距离（哈弗辛距离）
    :return: 两点间球面距离（单位：km）
    """
    R = 6371  # 地球平均半径（单位：km）
    
    # 将经纬度转换为弧度
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

# 计算距离矩阵，默认使用欧氏距离
def calculate_distance_matrix(data, distance_type='euclidean'):
    """
    计算所有点之间的距离矩阵
    :param data: 包含经纬度信息的DataFrame
    :param distance_type: 距离计算方法，可选 'euclidean', 'manhattan', 'chebyshev', 'haversine'
    :return: 距离矩阵
    """
    distance_functions = {
        'euclidean': euclidean_distance,
        'manhattan': manhattan_distance,
        'chebyshev': chebyshev_distance,
        'haversine': haversine_distance
    }
    # 检查距离类型是否支持
    if distance_type not in distance_functions:
        raise ValueError(f"不支持的距离类型: {distance_type}")
    # 获取距离函数
    distance_func = distance_functions[distance_type]
    # 初始化距离矩阵
    distance_matrix = np.zeros((len(data), len(data)))
    # 计算距离矩阵
    for i in range(len(data)):
        for j in range(len(data)):
            if distance_type == 'haversine':
                distance_matrix[i][j] = distance_func(
                    data["latitude"][i],
                    data["longitude"][i],
                    data["latitude"][j],
                    data["longitude"][j]
                )
            else:
                distance_matrix[i][j] = distance_func(
                    data["longitude"][i],
                    data["latitude"][i],
                    data["longitude"][j],
                    data["latitude"][j]
                )
                if distance_type != 'haversine':
                    # 将经纬度距离转换为实际距离(km)
                    distance_matrix[i][j] *= 111.32
    
    return distance_matrix

