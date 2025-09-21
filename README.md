# Forest Impact Simulator

A comprehensive Python Jupyter notebook for simulating the environmental impact of forest management activities including planting and clear-cutting operations.

## Features

- **Input Options**: Upload CSV or manually input land plot data
- **Management Modes**: Planting and clear-cutting simulations
- **Impact Calculations**: Carbon sequestration, biodiversity, forest resilience, water retention, air quality
- **Visualizations**: Charts and plots for environmental impacts
- **Export**: Results as CSV and JSON files

## Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Open the `forest_impact_simulator.ipynb` notebook in Jupyter
2. Run all cells to initialize the simulator
3. Load your data using one of the provided options:
   - Load sample data for demonstration
   - Upload a CSV file with your forest plot data
   - Enter data manually
4. Configure simulation parameters (mode, years, location)
5. Run the simulation
6. View visualizations and export results

## CSV File Format

Your CSV file should include these columns:

| Column | Description | Required |
|--------|-------------|----------|
| plot_id | Unique identifier for each plot | Yes |
| area | Area in hectares | Yes |
| tree_type | Type of trees (Oak, Pine, Maple, etc.) | Yes |
| tree_count | Number of trees | No |
| tree_density | Trees per hectare | No |
| latitude | GPS latitude | No |
| longitude | GPS longitude | No |
| soil_type | Soil classification | No |
| climate_zone | Climate zone | No |

## Supported Tree Types

- Oak, Pine, Maple, Birch, Spruce, Cedar, Redwood, Eucalyptus, Mixed, Other

## Environmental Impact Metrics

1. **Carbon Sequestration**: Based on tree type and count (kg CO₂/year)
2. **Biodiversity Impact**: Species diversity and ecosystem health score
3. **Forest Resilience**: Ability to withstand environmental stress
4. **Water Retention**: Water storage capacity (liters/year)
5. **Air Quality Improvement**: Particulate reduction percentage

## Management Modes

- **Planting Mode**: Simulates positive environmental impacts from adding trees
- **Clear-cutting Mode**: Simulates negative environmental impacts from removing trees

## Output Files

The simulator generates three export files:
1. **Detailed CSV**: Per-plot results with all metrics
2. **Summary CSV**: Aggregated totals and averages
3. **Complete JSON**: Full simulation data with metadata

## Sample Data

A sample CSV file (`sample_forest_data.csv`) is included for testing and demonstration purposes.

## License

MIT License - see LICENSE file for details.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the simulator.
