import matplotlib.pyplot as plt
# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 绘制路径图
def draw_figure(data, routes, figure_title, demands=None):
    """
    通用绘图函数，支持嵌套列表及扁平路径格式
    :param data: DataFrame 包含坐标
    :param routes: 路径列表，可以是 [[0,1,0], [0,2,0]] 或 [0,1,0,2,0]
    :param figure_title: 图标标题
    :param demands: 需求量列表（可选）
    """
    if demands is None:
        demands = data["demand"] if "demand" in data else [0] * len(data)

    plt.figure(figsize=(10, 10))
    plt.title(figure_title, fontsize=20)
    
    # 如果是扁平列表，自动转换为嵌套列表格式
    if routes and isinstance(routes[0], (int, np.integer)):
        from .IC import IC
        routes = IC.split_path_static(routes)

    for route in routes:
        if len(route) < 2: continue
        x = data["longitude"][route]
        y = data["latitude"][route]
        plt.plot(x, y, 'o-')
    
    # 在每个点上添加数字标签
    for i in range(len(data)):
        label = str(i)
        if i < len(demands):
            label += "|" + str(int(demands[i]))
        plt.text(data["longitude"][i], data["latitude"][i], label, fontsize=9, verticalalignment='bottom')
    
    # 用三角形标记配送中心
    plt.plot(data["longitude"][0], data["latitude"][0], 'r^', markersize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

# 为保持向下兼容提供别名
route_figure = draw_figure

# 绘制收敛曲线图
def convergence_curve(history_best_distance):
    print(len(history_best_distance))
    plt.figure(figsize=(10, 10))
    plt.plot(history_best_distance, marker='o')
    plt.title("Convergence Curve")
    plt.xlabel("Iteration")
    plt.ylabel("Best Distance")
    plt.grid()
    plt.show()
