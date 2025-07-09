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
    const routesTbody = document.getElementById('routes-tbody');
    const exportBtn = document.getElementById('export-btn');

    // Global variables to hold the state
    let uploadedFile = null;
    let myChart = null;
    let timerInterval = null;
    let previewOptions = null; // Store preview chart options

    /**
     * Initialize or reinitialize the chart
     */
    function initializeChart() {
        if (myChart) {
            myChart.dispose();
            myChart = null;
        }
        // Clear the container
        chartContainer.innerHTML = '';
        myChart = echarts.init(chartContainer);
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
     * Sends the uploaded file to the backend to get a preview chart.
     * @param {File} file - The uploaded Excel file.
     */
    async function previewData(file) {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/preview_data', { method: 'POST', body: formData });
            const result = await response.json();
            if (result.success) {
                // Parse the JSON string of chart options from the backend
                const chartOptions = JSON.parse(result.chart_options);
                previewOptions = chartOptions; // Store for later use
                console.log('Preview chart options:', chartOptions);
                // Initialize chart and set options
                initializeChart();
                myChart.setOption(chartOptions, true);
            } else {
                console.error('Preview failed:', result.error);
                alert('数据预览失败: ' + result.error);
            }
        } catch (error) {
            console.error('Preview request failed:', error);
            alert('数据预览请求失败: ' + error.message);
        }
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
            const response = await fetch('/upload_and_solve', { method: 'POST', body: formData });
            const result = await response.json();
            
            console.log('Algorithm response:', result);

            // Stop the timer
            clearInterval(timerInterval);
            
            if (result.success) {
                bestDistanceSpan.textContent = result.best_distance.toFixed(2);
                executionTimeSpan.textContent = `${result.execution_time.toFixed(1)} s`;

                // Display route details in the table
                routesTbody.innerHTML = '';
                if (result.route_details && result.route_details.length > 0) {
                    result.route_details.forEach((route, index) => {
                        const row = routesTbody.insertRow();
                        row.insertCell(0).textContent = index + 1; // ID
                        row.insertCell(1).textContent = route.path; // Route
                        row.insertCell(2).textContent = route.distance; // Length
                        row.insertCell(3).textContent = route.cargo; // Cargo
                    });
                    exportBtn.style.display = 'inline-block'; // Show export button
                } else {
                    exportBtn.style.display = 'none'; // Hide if no routes
                }
                
                // Parse chart options
                let chartOptions;
                if (typeof result.chart_options === 'string') {
                    chartOptions = JSON.parse(result.chart_options);
                } else {
                    chartOptions = result.chart_options;
                }
                
                console.log('Final chart options:', chartOptions);
                
                // Completely reinitialize chart to avoid any state accumulation
                initializeChart();
                
                // Set the new options
                myChart.setOption(chartOptions, true); // true means not merge, replace completely
                console.log('Chart set successfully');
                
            } else {
                console.error('Algorithm failed:', result.error);
                alert('算法执行失败: ' + result.error);
                bestDistanceSpan.textContent = '错误';
                executionTimeSpan.textContent = '错误';
            }
        } catch (error) {
            console.error('Algorithm request failed:', error);
            alert('请求失败: ' + error.message);
            bestDistanceSpan.textContent = '错误';
            executionTimeSpan.textContent = '错误';
        } finally {
            // Re-enable buttons
            executeBtn.disabled = false;
            clearBtn.disabled = false;
            executeBtn.textContent = '执行路径规划';
        }
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
