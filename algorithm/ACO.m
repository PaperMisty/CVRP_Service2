% 蚁群算法求解CVRP问题
function [bestRoute, minDist] = ACO_CVRP(excelFile, depot, vehicleCapacity, antNum, maxIter)
    % 从Excel文件读取客户数据
    data = readtable(excelFile);
    customers = [data.latitude data.longitude data.demand];  % 客户坐标和需求量
    customerNames = data.name;  % 客户名称
    n = size(customers,1);     % 客户点数量
    
    % 参数初始化
    pheromone = ones(n+1);     % 信息素矩阵
    alpha = 1;                 % 信息素重要程度因子
    beta = 5;                  % 启发式因子重要程度
    rho = 0.1;                 % 信息素挥发因子
    Q = 100;                   % 信息素增加强度系数
    
    % 计算距离矩阵
    D = zeros(n+1);
    for i = 1:n+1
        for j = 1:n+1
            if i == n+1
                p1 = depot;
            else
                p1 = customers(i,1:2);
            end
            if j == n+1
                p2 = depot;
            else
                p2 = customers(j,1:2);
            end
            D(i,j) = sqrt(sum((p1-p2).^2));
        end
    end
    
    % 初始化最优解
    bestRoute = [];
    minDist = inf;
    
    % 迭代寻找最优解
    for iter = 1:maxIter
        % 每只蚂蚁构建路径
        routes = cell(antNum,1);
        lengths = zeros(antNum,1);
        
        for ant = 1:antNum
            route = [];
            remain = 1:n;          % 待访问的客户点
            curLoad = vehicleCapacity;  % 当前车辆载重，初始为满载
            curPos = n+1;          % 当前位置(从仓库出发)
            
            while ~isempty(remain)
                % 计算转移概率
                p = zeros(1,length(remain));
                for i = 1:length(remain)
                    next = remain(i);
                    if curLoad >= customers(next,3)  % 确保当前载重能满足客户需求
                        p(i) = (pheromone(curPos,next)^alpha) * (1/D(curPos,next)^beta);
                    end
                end
                
                if sum(p) == 0     % 当前车辆无法服务剩余客户，需要回depot补货
                    route = [route n+1];  % 返回仓库
                    curPos = n+1;
                    curLoad = vehicleCapacity;  % 重新装满货物
                    continue;
                end
                
                % 轮盘赌选择下一个城市
                p = p/sum(p);
                r = rand();
                cum = 0;
                for i = 1:length(p)
                    cum = cum + p(i);
                    if r <= cum
                        next = remain(i);
                        break;
                    end
                end
                
                % 更新路径和载重
                route = [route next];
                remain(remain==next) = [];
                curLoad = curLoad - customers(next,3);  % 更新当前载重
                curPos = next;
                
                % 如果剩余载重不足以服务任何客户，则返回depot补货
                maxRemainDemand = min(customers(remain,3));
                if ~isempty(remain) && curLoad < maxRemainDemand
                    route = [route n+1];  % 返回仓库
                    curPos = n+1;
                    curLoad = vehicleCapacity;  % 重新装满货物
                end
            end
            route = [route n+1];   % 最后返回仓库
            
            % 计算路径长度
            routeLen = 0;
            for i = 1:length(route)-1
                routeLen = routeLen + D(route(i),route(i+1));
            end
            
            routes{ant} = route;
            lengths(ant) = routeLen;
        end
        
        % 更新最优解
        [minLen, minIdx] = min(lengths);
        if minLen < minDist
            minDist = minLen;
            bestRoute = routes{minIdx};
        end
        
        % 更新信息素
        deltaPheromone = zeros(n+1);
        for ant = 1:antNum
            route = routes{ant};
            for i = 1:length(route)-1
                deltaPheromone(route(i),route(i+1)) = deltaPheromone(route(i),route(i+1)) + Q/lengths(ant);
            end
        end
        pheromone = (1-rho)*pheromone + deltaPheromone;
    end
end
