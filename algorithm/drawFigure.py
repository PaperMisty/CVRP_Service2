import matplotlib.pyplot as plt
# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 绘制路径图
def draw_figure(data,routes,figure_title):
    plt.figure(figsize=(10, 10))
    plt.title(figure_title, fontsize=20)
    for route in routes:
        x = data["longitude"][route]
        y = data["latitude"][route]
        plt.plot(x, y, 'o-')
    # 在每个点上添加数字标签
    for i in range(len(data)):
        plt.text(data["longitude"][i], data["latitude"][i], str(i), fontsize=9, verticalalignment='bottom')
    # 用三角形标记配送中心
    plt.plot(data["longitude"][0], data["latitude"][0], 'r^')
    plt.show()

