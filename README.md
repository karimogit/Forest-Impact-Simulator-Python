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

## CSV File Formats

### Input CSV Format (for forest plot data)

Your input CSV file should include these columns:

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

### Output CSV Format (comprehensive results)

The simulator can export results in a comprehensive single-row CSV format containing:

**Metadata:**
- timestamp, simulator_version, simulation_years
- latitude, longitude, region coordinates
- soil_carbon_g_kg, soil_ph, soil_texture
- temperature_c, precipitation_mm

**Impact Results:**
- annual_carbon_sequestration_kg_co2_year, total_carbon_kg_co2
- biodiversity_impact, forest_resilience
- water_retention_percent, air_quality_improvement_percent
- average_biodiversity, average_resilience

**Planting Data:**
- area_hectares, total_trees, spacing_meters, density_trees_hectare
- years_to_complete, trees_per_season
- tree_names, tree_scientific_names, tree_carbon_rates_kg_co2_year, tree_percentages

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

A comprehensive sample CSV file (`sample-forest-planting-data.csv`) is included for testing and demonstration purposes. This file contains:

- **Complete simulation results** from a 50-year forest planting simulation
- **Real-world data** with coordinates in Belarus (52.54°N, 30.86°E)
- **Comprehensive metrics** including carbon sequestration, biodiversity, resilience, water retention, and air quality
- **Detailed planting information** for 69,632 Oak trees across 111.41 hectares
- **Environmental data** including temperature, soil conditions, and regional boundaries

The sample data demonstrates the full output format and can be used as a reference for understanding the simulator's capabilities and expected results.

## License

MIT License - see LICENSE file for details.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the simulator.
