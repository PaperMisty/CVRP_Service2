/**
 * CVRP Algorithms Library (JavaScript Version)
 * Ported from Python by Antigravity
 */

class CVRP_Algorithms {
    constructor(data, capacity) {
        this.data = data; // Array of objects {id, longitude, latitude, demand}
        this.capacity = capacity;
        this.n = data.length;
        this.distanceMatrix = this.createDistanceMatrix();
    }

    // 计算哈弗辛距离 (球面距离 km)
    haversineDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    createDistanceMatrix() {
        const matrix = Array.from({ length: this.n }, () => Array(this.n).fill(0));
        for (let i = 0; i < this.n; i++) {
            for (let j = 0; j < this.n; j++) {
                if (i === j) continue;
                // 默认使用 Haversine 保证与 Python 版本数量级一致
                matrix[i][j] = this.haversineDistance(
                    this.data[i].latitude, this.data[i].longitude,
                    this.data[j].latitude, this.data[j].longitude
                );
                
                // 留存欧氏距离作为备份，但需乘以 111.32 转换因子
                // const d = Math.sqrt(Math.pow(this.data[i].longitude - this.data[j].longitude, 2) + Math.pow(this.data[i].latitude - this.data[j].latitude, 2));
                // matrix[i][j] = d * 111.32;
            }
        }
        return matrix;
    }

    /** ------------------- Clark-Wright Savings ------------------- **/
    clarkWright() {
        const savings = [];
        const depot = 0;

        for (let i = 1; i < this.n; i++) {
            for (let j = i + 1; j < this.n; j++) {
                const s = this.distanceMatrix[depot][i] + this.distanceMatrix[depot][j] - this.distanceMatrix[i][j];
                savings.push({ i, j, s });
            }
        }

        savings.sort((a, b) => b.s - a.s);

        let routes = Array.from({ length: this.n - 1 }, (_, i) => [depot, i + 1, depot]);
        let demands = Array.from({ length: this.n - 1 }, (_, i) => this.data[i + 1].demand);

        for (const { i, j } of savings) {
            let ri_idx = -1, rj_idx = -1;
            let i_is_start = false, i_is_end = false;
            let j_is_start = false, j_is_end = false;

            for (let k = 0; k < routes.length; k++) {
                const r = routes[k];
                if (r.length === 3) { // [0, x, 0]
                    if (r[1] === i) {
                        ri_idx = k; i_is_start = i_is_end = true;
                    }
                    if (r[1] === j) {
                        rj_idx = k; j_is_start = j_is_end = true;
                    }
                } else {
                    if (r[1] === i) { ri_idx = k; i_is_start = true; }
                    else if (r[r.length - 2] === i) { ri_idx = k; i_is_end = true; }
                    
                    if (r[1] === j) { rj_idx = k; j_is_start = true; }
                    else if (r[r.length - 2] === j) { rj_idx = k; j_is_end = true; }
                }
            }

            if (ri_idx !== -1 && rj_idx !== -1 && ri_idx !== rj_idx) {
                if (demands[ri_idx] + demands[rj_idx] <= this.capacity) {
                    let merged = null;
                    const r1 = routes[ri_idx];
                    const r2 = routes[rj_idx];

                    if (i_is_end && j_is_start) {
                        merged = [...r1.slice(0, -1), ...r2.slice(1)];
                    } else if (i_is_start && j_is_start) {
                        const r1_rev = [0, ...r1.slice(1, -1).reverse(), 0];
                        merged = [...r1_rev.slice(0, -1), ...r2.slice(1)];
                    } else if (i_is_end && j_is_end) {
                        const r2_rev = [0, ...r2.slice(1, -1).reverse(), 0];
                        merged = [...r1.slice(0, -1), ...r2_rev.slice(1)];
                    } else if (i_is_start && j_is_end) {
                        const r1_rev = [0, ...r1.slice(1, -1).reverse(), 0];
                        const r2_rev = [0, ...r2.slice(1, -1).reverse(), 0];
                        merged = [...r1_rev.slice(0, -1), ...r2_rev.slice(1)];
                    }

                    if (merged) {
                        routes[ri_idx] = merged;
                        demands[ri_idx] += demands[rj_idx];
                        routes.splice(rj_idx, 1);
                        demands.splice(rj_idx, 1);
                    }
                }
            }
        }

        return routes;
    }

    /** ------------------- Nearest Neighbor (NNH) ------------------- **/
    nnh() {
        let visited = new Set([0]);
        let routes = [];
        
        while (visited.size < this.n) {
            let currentRoute = [0];
            let currentCapacity = 0;
            let currentNode = 0;
            
            while (true) {
                let nearest = -1;
                let minDist = Infinity;
                
                for (let i = 1; i < this.n; i++) {
                    if (!visited.has(i) && (currentCapacity + this.data[i].demand <= this.capacity + 1e-9)) {
                        const dist = this.distanceMatrix[currentNode][i];
                        if (dist < minDist) {
                            minDist = dist;
                            nearest = i;
                        }
                    }
                }
                
                if (nearest === -1) break;
                
                currentRoute.push(nearest);
                currentCapacity += this.data[nearest].demand;
                visited.add(nearest);
                currentNode = nearest;
            }
            currentRoute.push(0);
            routes.push(currentRoute);
        }
        return routes;
    }

    /** ------------------- Genetic Algorithm (GA) ------------------- **/
    ga(populationSize = 50, generations = 100, mutationRate = 0.1, crossoverRate = 0.8) {
        let population = this.initializeGaPopulation(populationSize);
        let bestIndiv = null;
        let bestDist = Infinity;

        for (let g = 0; g < generations; g++) {
            population = this.evolveGa(population, mutationRate, crossoverRate);
            for (const indiv of population) {
                const routes = this.splitRoutes(indiv);
                const dist = this.calcTotalDistance(routes);
                if (dist < bestDist) {
                    bestDist = dist;
                    bestIndiv = [...indiv];
                }
            }
        }
        return this.splitRoutes(bestIndiv);
    }

    initializeGaPopulation(size) {
        const nodes = Array.from({ length: this.n - 1 }, (_, i) => i + 1);
        return Array.from({ length: size }, () => {
            let p = [...nodes];
            for (let i = p.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [p[i], p[j]] = [p[j], p[i]];
            }
            return p;
        });
    }

    evolveGa(pop, mutationRate, crossoverRate) {
        let nextPop = [];
        pop.sort((a, b) => this.calcTotalDistance(this.splitRoutes(a)) - this.calcTotalDistance(this.splitRoutes(b)));
        nextPop.push(pop[0]); // Elitism

        while (nextPop.length < pop.length) {
            let p1 = this.tournamentSelection(pop);
            let p2 = this.tournamentSelection(pop);
            let child = Math.random() < crossoverRate ? this.orderedCrossover(p1, p2) : [...p1];
            if (Math.random() < mutationRate) this.swapMutation(child);
            nextPop.push(child);
        }
        return nextPop;
    }

    tournamentSelection(pop, k = 3) {
        let best = pop[Math.floor(Math.random() * pop.length)];
        for (let i = 1; i < k; i++) {
            let contender = pop[Math.floor(Math.random() * pop.length)];
            if (this.calcTotalDistance(this.splitRoutes(contender)) < this.calcTotalDistance(this.splitRoutes(best))) {
                best = contender;
            }
        }
        return best;
    }

    orderedCrossover(p1, p2) {
        const size = p1.length;
        const start = Math.floor(Math.random() * size);
        const end = Math.floor(Math.random() * (size - start)) + start;
        const child = Array(size).fill(-1);
        for (let i = start; i <= end; i++) child[i] = p1[i];
        let p2Idx = 0;
        for (let i = 0; i < size; i++) {
            if (child[i] === -1) {
                while (child.includes(p2[p2Idx])) p2Idx++;
                child[i] = p2[p2Idx];
            }
        }
        return child;
    }

    swapMutation(p) {
        const i = Math.floor(Math.random() * p.length);
        const j = Math.floor(Math.random() * p.length);
        [p[i], p[j]] = [p[j], p[i]];
    }

    // Split permutation into feasible routes
    splitRoutes(nodes) {
        let routes = [];
        let currentRoute = [0];
        let currentLoad = 0;
        for (const node of nodes) {
            const demand = this.data[node].demand;
            if (currentLoad + demand <= this.capacity + 1e-9) {
                currentRoute.push(node);
                currentLoad += demand;
            } else {
                currentRoute.push(0);
                routes.push(currentRoute);
                currentRoute = [0, node];
                currentLoad = demand;
            }
        }
        currentRoute.push(0);
        routes.push(currentRoute);
        return routes;
    }

    /** ------------------- Ant Colony Optimization (ACO) ------------------- **/
    aco(numAnts = 10, iterations = 20, alpha = 1, beta = 5, rho = 0.1) {
        let pheromones = Array.from({ length: this.n }, () => Array(this.n).fill(1));
        let bestRoutes = null;
        let bestDist = Infinity;

        for (let iter = 0; iter < iterations; iter++) {
            let allRoutes = [];
            for (let a = 0; a < numAnts; a++) {
                let routes = this.antBuildRoutes(pheromones, alpha, beta);
                let dist = this.calcTotalDistance(routes);
                if (dist < bestDist) {
                    bestDist = dist;
                    bestRoutes = routes;
                }
                allRoutes.push({ routes, dist });
            }
            // Update pheromones
            for (let i = 0; i < this.n; i++) {
                for (let j = 0; j < this.n; j++) {
                    pheromones[i][j] *= (1 - rho);
                }
            }
            for (const { routes, dist } of allRoutes) {
                const deposit = 1 / dist;
                for (const route of routes) {
                    for (let i = 0; i < route.length - 1; i++) {
                        pheromones[route[i]][route[i+1]] += deposit;
                    }
                }
            }
        }
        return bestRoutes;
    }

    antBuildRoutes(pheromones, alpha, beta) {
        let visited = new Set([0]);
        let routes = [];
        while (visited.size < this.n) {
            let route = [0];
            let load = 0;
            let current = 0;
            while (true) {
                let next = this.acoPickNext(current, visited, load, pheromones, alpha, beta);
                if (next === -1) break;
                route.push(next);
                load += this.data[next].demand;
                visited.add(next);
                current = next;
            }
            route.push(0);
            routes.push(route);
        }
        return routes;
    }

    acoPickNext(current, visited, load, pheromones, alpha, beta) {
        let probs = [];
        let total = 0;
        for (let i = 1; i < this.n; i++) {
            if (!visited.has(i) && (load + this.data[i].demand <= this.capacity + 1e-9)) {
                const tau = Math.pow(pheromones[current][i], alpha);
                const eta = Math.pow(1 / (this.distanceMatrix[current][i] || 0.0001), beta);
                const p = tau * eta;
                probs.push({ node: i, p });
                total += p;
            }
        }
        if (total === 0) return -1;
        let r = Math.random() * total;
        for (const prob of probs) {
            r -= prob.p;
            if (r <= 0) return prob.node;
        }
        return probs[probs.length - 1].node;
    }

    /** ------------------- 2-opt (IC) Improvement ------------------- **/
    improve(routes) {
        if (!routes) return [];
        const improvedRoutes = routes.map(route => {
            let improved = true;
            let path = [...route];
            // Only try to improve if it's a valid route with at least 4 nodes (0-a-b-0)
            if (path.length < 4) return path;
            
            let safeGuard = 0;
            while (improved && safeGuard < 100) {
                safeGuard++;
                improved = false;
                for (let i = 0; i < path.length - 3; i++) {
                    for (let j = i + 2; j < path.length - 1; j++) {
                        const d_old = this.distanceMatrix[path[i]][path[i+1]] + this.distanceMatrix[path[j]][path[j+1]];
                        const d_new = this.distanceMatrix[path[i]][path[j]] + this.distanceMatrix[path[i+1]][path[j+1]];
                        if (d_new < d_old) {
                            const segment = path.slice(i + 1, j + 1).reverse();
                            path.splice(i + 1, j - i, ...segment);
                            improved = true;
                        }
                    }
                }
            }
            return path;
        });
        return improvedRoutes;
    }

    /** ------------------- Common Interface ------------------- **/
    solve(algorithm, params = {}) {
        let routes;
        switch (algorithm) {
            case 'Clark-Wright': routes = this.clarkWright(); break;
            case 'NNH': routes = this.nnh(); break;
            case 'GA': routes = this.ga(params.population, params.generations, params.mutation, params.crossover); break;
            case 'ACO': routes = this.aco(params.ants, params.iterations, params.alpha, params.beta, params.rho); break;
            default: routes = this.clarkWright();
        }
        
        // Always try to improve with 2-opt
        routes = this.improve(routes);
        
        return {
            child_paths: routes,
            best_distance: this.calcTotalDistance(routes),
            distance_matrix: this.distanceMatrix
        };
    }

    calcTotalDistance(routes) {
        let total = 0;
        for (const route of routes) {
            for (let i = 0; i < route.length - 1; i++) {
                total += this.distanceMatrix[route[i]][route[i+1]];
            }
        }
        return total;
    }
}

window.CVRP_Algorithms = CVRP_Algorithms;
