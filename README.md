# Forest Impact Simulator (Python)

Python / Jupyter port of the [Forest Impact Simulator](https://github.com/karimogit/Forest-Impact-Simulator) web app.

Impact math (growth curves, clear-cutting carbon, biodiversity & resilience on a 1–5 scale, water/air percentages, planting timelines, CSV/JSON/GeoJSON export) is aligned with the original TypeScript implementation.

## Features

- **76 tree species** with carbon rates, biodiversity, and resilience values from the original app
- **Planting growth curve** (establishment → mature) and **clear-cutting** lifetime + lost-future carbon
- **Environmental impacts**: carbon, biodiversity, forest resilience, water retention %, air quality %
- **Social & land-use** scores matching the web app factors
- **Planting timeline** estimates by project scale
- **Exports**: comprehensive single-row CSV, JSON, GeoJSON (same schema as the web app)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Jupyter notebook

1. Open `forest_impact_simulator.ipynb`
2. Run all cells
3. Load sample data or your own CSV, configure mode/years, export results

### Python API

```python
from forest_impact import ForestImpactSimulator, format_area
from forest_impact.export import write_exports

sim = ForestImpactSimulator()
results = sim.simulate(
    trees=["Oak"],
    total_trees=69632,
    area_hectares=111.41,
    years=50,
    mode="planting",          # or "clear-cutting"
    latitude=52.54,
    longitude=30.86,
    temperature=21,
    spacing_meters=4,
)

print(format_area(results["plantingData"]["area"]))
print(results["impactResults"]["totalCarbon"])  # growth-curve cumulative kg CO₂
write_exports(results, "my_results")
```

## CSV formats

### Input (multi-plot)

| Column | Description | Required |
|--------|-------------|----------|
| plot_id | Plot identifier | No |
| area | Area in hectares | Yes |
| tree_type | Species name (e.g. Oak, Pine, Beech) | Yes |
| tree_count | Number of trees | No* |
| tree_density | Trees per hectare | No* |
| latitude / longitude | Location | No |

\* If both are missing, density defaults to 625 trees/ha (wide spacing).

### Output (comprehensive single-row)

Same headers as the web app export: metadata, soil/climate, impact metrics, planting data, and tree species fields (`tree_names`, `tree_scientific_names`, `tree_carbon_rates_kg_co2_year`, `tree_percentages`).

`annual_carbon_sequestration_kg_co2_year` is the **period average** (total ÷ years) under the planting growth curve — not the flat mature rate.

## Calculation notes

Aligned with the original README methodology:

- **Planting carbon**: `Σ(mature_rate × growth_factor(year))` for each year
- **Clear-cutting carbon**: lifetime stored carbon (by tree age) + lost future sequestration
- **Biodiversity / resilience**: 1–5 scale with time and stand-size bonuses
- **Water / air**: percentage metrics with progressive improvement or clear-cut degradation
- **Soil modifier**: `soil_carbon_g_kg × 0.1` kg CO₂/year added to the per-tree base before scaling

## Sample data

`sample-forest-planting-data.csv` is a 50-year Oak planting scenario (~111 ha, Belarus coordinates) regenerated with the aligned growth-curve totals.

## Tests

```bash
python tests/test_parity.py
```

## License

MIT — see [LICENSE](LICENSE).

## Related

- Original web app: https://github.com/karimogit/Forest-Impact-Simulator
