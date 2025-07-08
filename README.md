# CVRP (Capacitated Vehicle Routing Problem) Solver with Web Interface

This project provides a set of algorithms to solve the Capacitated Vehicle Routing Problem (CVRP) and a web-based user interface to interact with them. Users can upload an Excel file containing customer location and demand data, choose a solving algorithm, and visualize the resulting delivery routes.

## Project Structure

```
.
├── algorithm/                # Contains the core CVRP algorithms
│   ├── Clark_Wright.py       # Clark-Wright Savings algorithm
│   ├── IC.py                 # Improvement heuristic (local search)
│   ├── ACO_VRP.py            # (Placeholder) Ant Colony Optimization
│   ├── GA_VRP.py             # (Placeholder) Genetic Algorithm
│   ├── NNH_VRP.py            # (Placeholder) Nearest Neighbor Heuristic
│   └── ...
├── data/                     # Contains example data files
│   └── location_... .xlsx
├── web_app/                  # Contains the Flask web application
│   ├── static/
│   │   ├── css/style.css     # Styles for the web interface
│   │   └── js/script.js      # Frontend logic for interactivity
│   ├── templates/
│   │   └── index.html        # Main HTML page for the UI
│   └── app.py                # Flask backend server
└── README.md                 # This file
```

## Features

- **File Upload:** Users can drag-and-drop or select an Excel file with customer data.
- **Algorithm Selection:** A dropdown menu allows users to choose which CVRP algorithm to run. (Currently, only Clark-Wright Savings is fully integrated).
- **Dynamic Visualization:** The application uses the Pyecharts library to generate interactive charts.
  - **Preview:** Immediately after uploading a file, a scatter plot shows the distribution of customers, with bubble size and color corresponding to demand.
  - **Solution:** After running an algorithm, the chart displays the optimized delivery routes, with each route shown in a different color.
- **Interactive Tooltips:** Hovering over a customer node displays its ID and demand.

## How to Run

### 1. Prerequisites

- Python 3.x
- pip (Python package installer)

### 2. Installation

Clone the repository and navigate to the project directory. Then, install the required Python packages:

```bash
pip install flask pandas numpy openpyxl pyecharts
```

### 3. Running the Application

Once the dependencies are installed, you can start the Flask web server by running:

```bash
python web_app/app.py
```

The server will start, and you can access the web interface by navigating to the following URL in your web browser:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

### 4. Using the Interface

1.  **Upload Data:** Drag and drop an Excel file onto the designated area, or click "Select File" to browse for it.
2.  **Format:** The Excel file must contain columns named `longitude`, `latitude`, and `demand`. The first row (index 0) is treated as the depot.
3.  **Select Algorithm:** Choose an algorithm from the dropdown menu.
4.  **Set Capacity:** Enter the vehicle capacity.
5.  **Execute:** Click the "Execute" button to run the algorithm and visualize the solution.
