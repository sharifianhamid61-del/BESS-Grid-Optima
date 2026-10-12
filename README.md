# BESS-Grid-Optima
**Geospatial Power Grid Optimization & BESS Integration Toolkit**

This project provides an automated pipeline for optimizing Battery Energy Storage System (BESS) capacity and placement within distribution grids. It leverages `pandapower` for power flow analysis and geospatial libraries for grid visualization.

## Features
- **Power Flow Simulation:** Automated calculation of grid constraints using `pandapower`.
- **Optimization Pipeline:** Iterative BESS capacity sizing to minimize peak feeder load and voltage deviations.
- **Geospatial Visualization:** Integrated mapping of grid assets and optimal BESS location.
- **Technical Dashboards:** Automated generation of analysis reports including load profiles, dispatch schedules, and loss reduction metrics.

## Tech Stack
- **Language:** Python 3.x
- **Core Libraries:** `pandapower` (Grid Analysis), `pandas`/`numpy` (Data Processing), `matplotlib` (Visualization).
- **Geospatial:** `geopandas`, `shapely`.

## Project Structure
- `main.py`: Entry point for the optimization pipeline.
- `visualizer.py`: Custom dashboard generator for technical analysis.
- `data/`: Grid topology and load profile datasets.

## Getting Started
1. Clone the repository: `git clone https://github.com/sharifianhamid61-del/BESS-Grid-Optima.git`
2. Install requirements: `pip install -r requirements.txt`
3. Run the optimization: `python main.py`

## Contact
**Hamid Sharifian**
M.Sc. Electrical Power Engineer
Email: [sharifian.hamid61@gmail.com](mailto:sharifian.hamid61@gmail.com)
LinkedIn: [linkedin.com/in/hamid-sharifian-4b349052](https://www.linkedin.com/in/hamid-sharifian-4b349052)
