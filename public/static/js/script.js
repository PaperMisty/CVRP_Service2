document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the necessary DOM elements
    const dropArea = document.getElementById('drop-area');
    const fileElem = document.getElementById('fileElem');
    const fileSelect = document.getElementById('fileSelect');
    const fileNameSpan = document.getElementById('fileName');
    const executeBtn = document.getElementById('execute-btn');
    const clearBtn = document.getElementById('clear-btn');
    const algorithmSelect = document.getElementById('algorithm-select');
    const capacityInput = document.getElementById('capacity-input');
    const bestDistanceSpan = document.getElementById('best-distance');
    const executionTimeSpan = document.getElementById('execution-time');
    const chartContainer = document.getElementById('chart-container');
    const heatmapContainer = document.getElementById('heatmap-container');
    const routesTbody = document.getElementById('routes-tbody');
    const exportBtn = document.getElementById('export-btn');
    const exportHeatmapBtn = document.getElementById('export-heatmap-btn');
    const exportChartBtn = document.getElementById('export-chart-btn');

    // Global variables to hold the state
    let uploadedFile = null;
    let myChart = null;
    let heatmapChart = null;
    let timerInterval = null;
    let previewOptions = null; // Store preview chart options
    let currentDistanceMatrix = null; // Store the distance matrix
    let currentData = null; // Store the parsed Excel data

    /**
     * Initialize or reinitialize the chart
     */
    function initializeChart() {
        if (myChart) {
            myChart.dispose();
            myChart = null;
        }
        if (heatmapChart) {
            heatmapChart.dispose();
            heatmapChart = null;
        }
        // Clear the containers
        chartContainer.innerHTML = '';
        heatmapContainer.innerHTML = '';
        myChart = echarts.init(chartContainer);
        heatmapChart = echarts.init(heatmapContainer);
    }

    /**
     * Resets the application state and clears the UI.
     */
    function resetState() {
        bestDistanceSpan.textContent = 'N/A';
        executionTimeSpan.textContent = 'N/A';
        previewOptions = null;
        initializeChart();
    }

    /**
     * Clears algorithm results while keeping the preview chart.
     * Used before running a new algorithm to prevent accumulation.
     */
    function clearAlgorithmResults() {
        bestDistanceSpan.textContent = 'N/A';
        executionTimeSpan.textContent = 'N/A';
        routesTbody.innerHTML = ''; // Clear route details
        exportBtn.style.display = 'none'; // Hide export button
        exportHeatmapBtn.style.display = 'none'; // Hide heatmap export button
        exportChartBtn.style.display = 'none'; // Hide chart export button
        currentDistanceMatrix = null;
        // Show preview chart if available
        if (previewOptions && uploadedFile) {
            initializeChart();
            myChart.setOption(previewOptions, true); // true means not merge, replace completely
        } else {
            resetState();
        }
    }

    /**
     * Handles file selection from either drag-and-drop or file input.
     * @param {FileList} files - The list of files selected by the user.
     */
    function handleFiles(files) {
        if (files.length > 0) {
            uploadedFile = files[0];
            fileNameSpan.textContent = uploadedFile.name;
            resetState();
            previewData(uploadedFile);
        } else {
            uploadedFile = null;
            fileNameSpan.textContent = '未选择文件';
            resetState();
        }
    }

    /**
     * Parsing the Excel file locally and creating a preview.
     * @param {File} file - The uploaded Excel file.
     */
    async function previewData(file) {
        try {
            const data = await file.arrayBuffer();
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet);

            // Robust Mapping: Identify columns by common names
            const findColumn = (obj, possibleNames) => {
                const keys = Object.keys(obj);
                for (const name of possibleNames) {
                    const match = keys.find(k => k.toLowerCase().includes(name.toLowerCase()));
                    if (match) return match;
                }
                return null;
            };

            const firstRow = jsonData[0];
            const lonCol = findColumn(firstRow, ['longitude', 'lon', '经度', 'lng']);
            const latCol = findColumn(firstRow, ['latitude', 'lat', '纬度']);
            const demCol = findColumn(firstRow, ['demand', '需求', 'weight', 'cargo']);

            if (!lonCol || !latCol) {
                throw new Error('Excel 文件格式错误：未找到经纬度列（longitude/latitude）。');
            }

            currentData = jsonData.map((row, index) => ({
                id: index,
                longitude: parseFloat(row[lonCol]),
                latitude: parseFloat(row[latCol]),
                demand: demCol ? parseFloat(row[demCol] || 0) : 0
            }));

            // Filter out invalid rows
            currentData = currentData.filter(d => !isNaN(d.longitude) && !isNaN(d.latitude));
            
            if (currentData.length === 0) throw new Error('Excel 文件中没有有效的坐标数据。');

            console.log('Parsed data:', currentData);

            // Create preview chart options manually (mimicking backend create_route_chart)
            const chartOptions = createPreviewOptions(currentData);
            previewOptions = chartOptions;

            initializeChart();
            myChart.setOption(chartOptions, true);
        } catch (error) {
            console.error('Local preview failed:', error);
            alert('数据解析失败: ' + error.message);
        }
    }

    function createPreviewOptions(data) {
        return {
            title: { text: "CVRP Data Preview" },
            tooltip: { trigger: 'item' },
            xAxis: { type: 'value', scale: true, name: 'Longitude' },
            yAxis: { type: 'value', scale: true, name: 'Latitude' },
            series: [{
                type: 'scatter',
                data: data.map(d => [d.longitude, d.latitude]),
                symbolSize: 10,
                itemStyle: {
                    color: (params) => params.dataIndex === 0 ? '#ff0000' : '#007bff'
                },
                label: {
                    show: true,
                    formatter: (params) => data[params.dataIndex].id + (data[params.dataIndex].demand > 0 ? `|${data[params.dataIndex].demand}` : '')
                }
            }]
        };
    }

    /**
     * Sends the file and algorithm parameters to the backend to run the solver.
     * Renders the resulting chart with solution routes.
     */
    async function executeAlgorithm() {
        if (!uploadedFile) {
            alert('请先上传 Excel 文件！');
            return;
        }

        // Disable buttons to prevent multiple clicks
        executeBtn.disabled = true;
        clearBtn.disabled = true;
        executeBtn.textContent = '正在计算...';
        
        // Clear previous algorithm results before running new one
        bestDistanceSpan.textContent = '计算中...';
        executionTimeSpan.textContent = '计时中...';

        // Start the timer
        let startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
            executionTimeSpan.textContent = `${elapsedTime} s`;
        }, 100);
        
    const formData = new FormData();
    formData.append('file', uploadedFile);
    const algorithm = algorithmSelect.value;
    formData.append('algorithm', algorithm);
    formData.append('capacity', capacityInput.value);

    // Append algorithm-specific parameters
    if (algorithm === 'ACO') {
        formData.append('aco_ants', document.getElementById('aco-ants').value);
        formData.append('aco_iterations', document.getElementById('aco-iterations').value);
        formData.append('aco_alpha', document.getElementById('aco-alpha').value);
        formData.append('aco_beta', document.getElementById('aco-beta').value);
        formData.append('aco_rho', document.getElementById('aco-rho').value);
    } else if (algorithm === 'GA') {
        const gaPopulationInput = document.getElementById('ga-population');
        const gaGenerationsInput = document.getElementById('ga-generations');
        const gaPopulation = parseInt(gaPopulationInput.value, 10);
        const gaGenerations = parseInt(gaGenerationsInput.value, 10);

        // Final validation before execution
        if (gaPopulation > 500 || gaGenerations > 500) {
            alert('“种群数量”和“迭代次数”都不能大于 500。请修正后再试。');
            // Reset UI state
            executeBtn.disabled = false;
            clearBtn.disabled = false;
            executeBtn.textContent = '执行路径规划';
            bestDistanceSpan.textContent = 'N/A';
            executionTimeSpan.textContent = 'N/A';
            clearInterval(timerInterval);
            // Correct the values in the input fields
            if (gaPopulation > 500) gaPopulationInput.value = 500;
            if (gaGenerations > 500) gaGenerationsInput.value = 500;
            return; // Stop execution
        }

        formData.append('ga_population', gaPopulation);
        formData.append('ga_generations', gaGenerations);
        formData.append('ga_mutation', document.getElementById('ga-mutation').value);
        formData.append('ga_crossover', document.getElementById('ga-crossover').value);
    }

        try {
            // Local calculation starts here
            const capacity = parseInt(capacityInput.value, 10);
            const algorithm = algorithmSelect.value;
            const params = {};

            if (algorithm === 'ACO') {
                params.ants = parseInt(document.getElementById('aco-ants').value, 10);
                params.iterations = parseInt(document.getElementById('aco-iterations').value, 10);
                params.alpha = parseFloat(document.getElementById('aco-alpha').value);
                params.beta = parseFloat(document.getElementById('aco-beta').value);
                params.rho = parseFloat(document.getElementById('aco-rho').value);
            } else if (algorithm === 'GA') {
                params.population = parseInt(document.getElementById('ga-population').value, 10);
                params.generations = parseInt(document.getElementById('ga-generations').value, 10);
                params.mutation = parseFloat(document.getElementById('ga-mutation').value);
                params.crossover = parseFloat(document.getElementById('ga-crossover').value);
            }

            // Small delay to allow UI to update (spinner)
            await new Promise(resolve => setTimeout(resolve, 100));

            const solver = new CVRP_Algorithms(currentData, capacity);
            const result = solver.solve(algorithm, params);
            
            console.log('Local calculation result:', result);

            // Stop the timer
            clearInterval(timerInterval);
            const endTime = Date.now();
            const executionTime = (endTime - startTime) / 1000;
            executionTimeSpan.textContent = `${executionTime.toFixed(1)} s`;

            bestDistanceSpan.textContent = result.best_distance.toFixed(2);

            // Display route details in the table
            routesTbody.innerHTML = '';
            const routeDetails = calculateRouteDetails(result.child_paths, result.distance_matrix, currentData);
            
            routeDetails.forEach((route, index) => {
                const row = routesTbody.insertRow();
                row.insertCell(0).textContent = index + 1; // ID
                row.insertCell(1).textContent = route.path; // Route
                row.insertCell(2).textContent = route.distance.toFixed(2); // Length
                row.insertCell(3).textContent = route.cargo.toFixed(2); // Cargo
            });
            exportBtn.style.display = 'inline-block';

            // Generate chart options for the solution
            const chartOptions = createSolutionOptions(currentData, result.child_paths, `CVRP Solution - ${algorithm}`);
            
            initializeChart();
            myChart.setOption(chartOptions, true);
            exportChartBtn.style.display = 'inline-block';

            // Render heatmap
            currentDistanceMatrix = result.distance_matrix;
            renderHeatmap(currentDistanceMatrix);
            exportHeatmapBtn.style.display = 'inline-block';
            
        } catch (error) {
            console.error('Calculation failed:', error);
            alert('计算失败: ' + error.message);
            bestDistanceSpan.textContent = '错误';
            executionTimeSpan.textContent = '错误';
            clearInterval(timerInterval);
        } finally {
            executeBtn.disabled = false;
            clearBtn.disabled = false;
            executeBtn.textContent = '执行路径规划';
        }
    }

    function calculateRouteDetails(routes, matrix, data) {
        return routes.map(route => {
            let dist = 0;
            let cargo = 0;
            for (let i = 0; i < route.length - 1; i++) {
                dist += matrix[route[i]][route[i+1]];
                if (route[i] !== 0) cargo += data[route[i]].demand;
            }
            return {
                path: route.join(' → '),
                distance: dist,
                cargo: cargo
            };
        });
    }

    function createSolutionOptions(data, routes, title) {
        const series = [{
            type: 'scatter',
            data: data.map(d => [d.longitude, d.latitude]),
            symbolSize: 10,
            itemStyle: {
                color: (params) => params.dataIndex === 0 ? '#ff0000' : '#007bff'
            },
            label: {
                show: true,
                formatter: (params) => data[params.dataIndex].id
            },
            zIndex: 10
        }];

        routes.forEach((route, index) => {
            const lineData = route.map(nodeIdx => [data[nodeIdx].longitude, data[nodeIdx].latitude]);
            series.push({
                type: 'line',
                data: lineData,
                smooth: false,
                lineStyle: { width: 2, opacity: 0.8 },
                symbol: 'none',
                name: `Route ${index + 1}`
            });
        });

        return {
            title: { text: title },
            tooltip: { trigger: 'item' },
            legend: { show: false },
            xAxis: { type: 'value', scale: true },
            yAxis: { type: 'value', scale: true },
            series: series
        };
    }

    // Event Listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
    });
    dropArea.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
    fileSelect.addEventListener('click', () => fileElem.click());
    fileElem.addEventListener('change', (e) => handleFiles(e.target.files));
    executeBtn.addEventListener('click', executeAlgorithm);
    clearBtn.addEventListener('click', clearAlgorithmResults);

    // Show/hide algorithm parameters based on selection
    const acoParams = document.getElementById('aco-params');
    const gaParams = document.getElementById('ga-params');
    algorithmSelect.addEventListener('change', () => {
        const selected = algorithmSelect.value;
        acoParams.style.display = selected === 'ACO' ? 'block' : 'none';
        gaParams.style.display = selected === 'GA' ? 'block' : 'none';
    });
    // Trigger change event on load to set initial state
    algorithmSelect.dispatchEvent(new Event('change'));

    // Real-time validation for GA parameters
    const gaPopulationInput = document.getElementById('ga-population');
    const gaGenerationsInput = document.getElementById('ga-generations');

    gaPopulationInput.addEventListener('input', () => {
        const value = parseInt(gaPopulationInput.value, 10);
        if (value > 500) {
            alert('“种群数量”不能大于 500。');
            gaPopulationInput.value = 500;
        }
    });

    gaGenerationsInput.addEventListener('input', () => {
        const value = parseInt(gaGenerationsInput.value, 10);
        if (value > 500) {
            alert('“迭代次数”不能大于 500。');
            gaGenerationsInput.value = 500;
        }
    });

    // Export to Excel functionality
    exportBtn.addEventListener('click', () => {
        const table = document.getElementById('routes-table');
        const wb = XLSX.utils.table_to_book(table, { sheet: "Route Details" });
        XLSX.writeFile(wb, "route_details.xlsx");
    });

    exportHeatmapBtn.addEventListener('click', () => {
        if (currentDistanceMatrix) {
            const ws = XLSX.utils.aoa_to_sheet(currentDistanceMatrix);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Distance Matrix");
            XLSX.writeFile(wb, "distance_matrix.xlsx");
        }
    });

    exportChartBtn.addEventListener('click', () => {
        if (myChart) {
            const url = myChart.getDataURL({
                type: 'png',
                pixelRatio: 2,
                backgroundColor: '#fff'
            });
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cvrp_solution_chart.png';
            a.click();
        }
    });

    function renderHeatmap(matrix) {
        const data = [];
        let maxDist = 0;
        for (let i = 0; i < matrix.length; i++) {
            for (let j = 0; j < matrix[i].length; j++) {
                data.push([i, j, matrix[i][j].toFixed(2)]);
                if (matrix[i][j] > maxDist) {
                    maxDist = matrix[i][j];
                }
            }
        }

        const option = {
            tooltip: {
                position: 'top',
                formatter: params => `From ${params.value[0]} to ${params.value[1]}: ${params.value[2]} km`
            },
            grid: {
                height: '80%',
                top: '10%'
            },
            xAxis: {
                type: 'category',
                data: Array.from({ length: matrix.length }, (_, i) => i),
                splitArea: {
                    show: true
                }
            },
            yAxis: {
                type: 'category',
                data: Array.from({ length: matrix.length }, (_, i) => i),
                splitArea: {
                    show: true
                }
            },
            visualMap: {
                min: 0,
                max: maxDist,
                calculable: true,
                orient: 'vertical',
                left: 'right',
                top: 'center'
            },
            series: [{
                name: 'Distance',
                type: 'heatmap',
                data: data,
                label: {
                    show: matrix.length < 20 // Only show labels for small matrices
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        };
        heatmapChart.setOption(option);
    }

    // Accordion functionality
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    // Function to open a specific accordion item
    function openAccordion(header) {
        const content = header.nextElementSibling;
        header.classList.add('active');
        content.style.maxHeight = content.scrollHeight + 'px';
    }

    // Function to close a specific accordion item
    function closeAccordion(header) {
        const content = header.nextElementSibling;
        header.classList.remove('active');
        content.style.maxHeight = null;
    }

    // Set the first item to be open by default
    if (accordionHeaders.length > 0) {
        const firstHeader = accordionHeaders[0];
        // We need to set the maxHeight to its scrollHeight to make it visible
        // The class 'active' is already set in the HTML
        const firstContent = firstHeader.nextElementSibling;
        firstContent.style.maxHeight = firstContent.scrollHeight + 'px';
    }

    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const isActive = header.classList.contains('active');
            
            // Close all accordions
            accordionHeaders.forEach(h => closeAccordion(h));

            // If the clicked header was not active, open it
            if (!isActive) {
                openAccordion(header);
            }
        });
    });
});
