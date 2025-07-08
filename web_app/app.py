import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import sys

# Add the parent directory to the sys.path to allow importing modules from 'algorithm'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algorithm.Clark_Wright import CVRP_CW
from algorithm.ACO_VRP import CVRP_ACO
from algorithm.GA_VRP import CVRP_GA
from algorithm.NNH_VRP import CVRP_NNH
import algorithm.IC as IC
from pyecharts import options as opts
from pyecharts.charts import Scatter
from pyecharts.globals import ChartType, SymbolType
from pyecharts.commons.utils import JsCode
import json
import time
from flask import send_from_directory

app = Flask(__name__, template_folder='templates', static_folder='static')

def process_excel_file(file):
    """Helper function to read and validate Excel data."""
    df = pd.read_excel(file)
    required_columns = ["longitude", "latitude", "demand"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
        df[col] = df[col].astype(float)
    return df

def create_pyecharts_base(df, title):
    scatter_data = df[['longitude', 'latitude', 'demand']].values.tolist()

    # 计算坐标轴范围，留出10%的边距
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    c = (
        Scatter()
        .add_xaxis(xaxis_data=[])
        .add_yaxis(
            series_name="Customers",
            y_axis=scatter_data,
            symbol_size=10,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_series_opts(
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode("function (params) { return 'ID: ' + params.dataIndex + '<br/>Demand: ' + params.value[2]; }")
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                type_="value",
                name="Longitude",
                min_=lon_min - 0.1 * lon_range,
                max_=lon_max + 0.1 * lon_range,
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                name="Latitude",
                min_=lat_min - 0.1 * lat_range,
                max_=lat_max + 0.1 * lat_range,
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
            visualmap_opts=opts.VisualMapOpts(
                is_show=True,
                min_=int(df['demand'].min()),
                max_=int(df['demand'].max()),
                dimension=2,
                orient="vertical",
                pos_left="right",
                pos_top="center",
                range_color=["#e0ffff", "#006edd"],
            ),
        )
    )
    
    # 添加仓库点（红色显示）
    depot = df.iloc[0]
    c.add_yaxis(
        series_name="Depot",
        y_axis=[[depot['longitude'], depot['latitude'], depot['demand']]],
        symbol_size=20,
        itemstyle_opts=opts.ItemStyleOpts(color='red'),
        label_opts=opts.LabelOpts(is_show=False),
    )

    return c

def create_route_chart(df, child_paths, title):
    """创建包含路线的完整图表 - 完全重新构建，避免状态累积"""
    # 预定义颜色列表
    colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
    
    # 创建基础散点图数据
    scatter_data = df[['longitude', 'latitude', 'demand']].values.tolist()
    
    # 计算坐标轴范围
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min
    
    # 确保边距至少为0.01，避免除零错误
    if lon_range == 0:
        lon_range = 0.01
    if lat_range == 0:
        lat_range = 0.01
    
    # 构建图例数据
    legend_data = ["Customers", "Depot"]
    if child_paths:
        legend_data.extend([f"Route {i+1}" for i in range(len(child_paths))])
    
    # 构建完整的图表配置 - 每次都创建全新的配置对象
    option = {
        "animation": False,  # 禁用动画避免状态混乱
        "title": {"text": title},
        "tooltip": {"trigger": "item"},
        "legend": {
            "data": legend_data,
            "top": "bottom"
        },
        "xAxis": {
            "type": "value",
            "name": "Longitude",
            "min": lon_min - 0.1 * lon_range,
            "max": lon_max + 0.1 * lon_range,
            "splitLine": {"show": True}
        },
        "yAxis": {
            "type": "value", 
            "name": "Latitude",
            "min": lat_min - 0.1 * lat_range,
            "max": lat_max + 0.1 * lat_range,
            "splitLine": {"show": True}
        },
        "visualMap": {
            "show": True,
            "min": int(df['demand'].min()),
            "max": int(df['demand'].max()),
            "dimension": 2,
            "orient": "vertical",
            "left": "right",
            "top": "center",
            "inRange": {"color": ["#e0ffff", "#006edd"]}
        },
        "series": []  # 确保series数组为空开始
    }
    
    # 添加客户点散点图
    option["series"].append({
        "name": "Customers",
        "type": "scatter",
        "data": [row[:] for row in scatter_data],  # 创建深拷贝
        "symbolSize": 10,
        "itemStyle": {"color": colors[0]},
        "tooltip": {
            "formatter": "ID: {dataIndex}<br/>Demand: {value[2]}"
        }
    })
    
    # 添加仓库点
    depot = df.iloc[0]
    option["series"].append({
        "name": "Depot",
        "type": "scatter", 
        "data": [[float(depot['longitude']), float(depot['latitude']), float(depot['demand'])]],
        "symbolSize": 20,
        "itemStyle": {"color": "red"},
        "tooltip": {
            "formatter": "Depot<br/>Demand: {value[2]}"
        }
    })
    
    # 添加路线
    if child_paths:
        for i, route in enumerate(child_paths):
            # 移除路线中的仓库点（0），然后在首尾添加仓库点
            customer_route = [node for node in route if node != 0]
            full_route = [0] + customer_route + [0]
            
            # 创建路线坐标数据
            route_coords = []
            for node_idx in full_route:
                if node_idx < len(df):  # 边界检查
                    node = df.iloc[node_idx]
                    route_coords.append([float(node['longitude']), float(node['latitude'])])
            
            # 添加路线系列
            if route_coords and len(route_coords) > 1:  # 确保路线有效
                option["series"].append({
                    "name": f"Route {i+1}",
                    "type": "line",
                    "data": route_coords,
                    "lineStyle": {
                        "width": 3,
                        "color": colors[(i + 2) % len(colors)]
                    },
                    "symbol": "arrow",
                    "symbolSize": 8,
                    "showSymbol": True,
                    "tooltip": {
                        "formatter": f"Route {i+1}"
                    }
                })
    
    # 返回JSON字符串，确保没有引用问题
    return json.dumps(option, ensure_ascii=False)

@app.route('/')
def index():
    return render_template('index.html', now=time.time())

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(os.path.join(app.static_folder, 'data'), filename, as_attachment=True)

@app.route('/preview_data', methods=['POST'])
def preview_data():
    """Endpoint to handle file upload and return a preview chart of node locations."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        try:
            # Process the uploaded file
            df = process_excel_file(file)
            # Create the base chart with node locations
            chart = create_pyecharts_base(df, "Customer Distribution Preview")
            # Return the chart options as a JSON-compliant string
            return jsonify({"success": True, "chart_options": chart.dump_options_with_quotes()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/upload_and_solve', methods=['POST'])
def upload_and_solve():
    """Endpoint to run the selected CVRP algorithm and return the solution chart."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        try:
            print("Processing file...")
            df = process_excel_file(file)
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"First few rows:\n{df.head()}")
            
            algorithm_choice = request.form.get('algorithm', 'Clark-Wright')
            capacity = float(request.form.get('capacity', 20))
            print(f"Algorithm: {algorithm_choice}, Capacity: {capacity}")

            # --- Algorithm Execution ---
            start_time = time.time()
            child_paths = []
            best_distance = float('inf')

            if algorithm_choice == 'Clark-Wright':
                print("Running Clark-Wright algorithm...")
                cvrp_solver = CVRP_CW(data=df, capacity=capacity)
                initial_path, _, distance_matrix = cvrp_solver.run()
                
                print("Running IC improvement for Clark-Wright...")
                ic_solver = IC.IC(distance_matrix, initial_path)
                ic_solver.split_path()
                child_paths, best_distance = ic_solver.improve()

            elif algorithm_choice == 'ACO':
                print("Running ACO algorithm...")
                ants = request.form.get('aco_ants', 10)
                iterations = request.form.get('aco_iterations', 20)
                alpha = request.form.get('aco_alpha', 1.0)
                beta = request.form.get('aco_beta', 5.0)
                rho = request.form.get('aco_rho', 0.5)
                aco_solver = CVRP_ACO(data=df, num_ants=ants, num_iterations=iterations, alpha=alpha, beta=beta, rho=rho, capacity=capacity)
                initial_path, _, distance_matrix = aco_solver.run()

                print("Running IC improvement for ACO...")
                ic_solver = IC.IC(distance_matrix, initial_path)
                ic_solver.split_path()
                child_paths, best_distance = ic_solver.improve()

            elif algorithm_choice == 'GA':
                print("Running GA algorithm...")
                population = int(request.form.get('ga_population', 50))
                generations = int(request.form.get('ga_generations', 100))

                # Server-side validation
                if population > 500 or generations > 500:
                    error_msg = []
                    if population > 500:
                        error_msg.append("“种群数量”不能大于 500。")
                    if generations > 500:
                        error_msg.append("“迭代次数”不能大于 500。")
                    return jsonify({"error": " ".join(error_msg)}), 400

                mutation = request.form.get('ga_mutation', 0.1)
                crossover = request.form.get('ga_crossover', 0.8)
                ga_solver = CVRP_GA(data=df, population=population, num_generations=generations, mutation_rate=mutation, crossover_rate=crossover, capacity=capacity)
                initial_path, _, distance_matrix = ga_solver.run()

                print("Running IC improvement for GA...")
                ic_solver = IC.IC(distance_matrix, initial_path)
                ic_solver.split_path()
                child_paths, best_distance = ic_solver.improve()

            elif algorithm_choice == 'NNH':
                print("Running NNH algorithm...")
                nnh_solver = CVRP_NNH(data=df, vehicle_capacity=capacity)
                initial_path, _, distance_matrix = nnh_solver.solve()

                print("Running IC improvement for NNH...")
                ic_solver = IC.IC(distance_matrix, initial_path)
                ic_solver.split_path()
                child_paths, best_distance = ic_solver.improve()

            else:
                return jsonify({"error": "Invalid algorithm selected"}), 400

            # --- Debugging Output ---
            print(f"Algorithm: {algorithm_choice}")
            print(f"Routes found: {len(child_paths)}")
            print(f"Child paths: {child_paths}")
            print(f"Best distance: {best_distance}")

            # --- Chart Generation ---
            print("Creating route chart...")
            # 使用完全重新构建的图表生成方法
            chart_options = create_route_chart(df, child_paths, f"CVRP Solution - {algorithm_choice}")
            print("Chart creation successful")

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Total execution time: {execution_time:.2f}s")

            # --- Calculate Route Details ---
            route_details = []
            for i, route in enumerate(child_paths):
                route_dist = 0
                route_demand = 0
                full_route = [0] + [node for node in route if node != 0] + [0]
                for j in range(len(full_route) - 1):
                    start_node = full_route[j]
                    end_node = full_route[j+1]
                    route_dist += distance_matrix[start_node][end_node]
                for node_idx in route:
                    if node_idx != 0:
                        route_demand += df.loc[node_idx, 'demand']
                
                route_details.append({
                    "name": f"Route {i+1}",
                    "path": " -> ".join(map(str, full_route)),
                    "distance": round(route_dist, 2),
                    "cargo": round(route_demand, 2)
                })

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Total execution time: {execution_time:.2f}s")

            # Return the final chart options and the total distance
            return jsonify({
                "success": True,
                "best_distance": best_distance,
                "execution_time": execution_time,
                "chart_options": chart_options,
                "route_details": route_details
            })
        except Exception as e:
            import traceback
            print(f"Error in upload_and_solve: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")  # 打印完整堆栈信息
            return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
