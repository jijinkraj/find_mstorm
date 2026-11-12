# Geomagnetic Storm Identification Tool

Identifies and visualizes geomagnetic storms from SYM-H data.

## Quick Start

```bash
# Download data from OMNIWeb
make download START=240101 END=260101

# Run storm identification
make storm

# Generate single overview plot
make allplot
```

## CLI Usage

```
python3 src/mstorm.py [OPTIONS] [DATA_FILE]

Options:
  --llimit N, -ll N  Link limit in minutes (default: 60)
  --all         Generate single overview plot instead of per-storm plots

Arguments:
  DATA_FILE     Path to SYM-H data file (default: data/data.txt)
```

## Data Download

```bash
./src/download_symh.py <start_date> <end_date>
# Dates in YYMMDD format:
./src/download_symh.py 240101 260101
```

Data is saved to `data/data.txt` in 5-column format: `Year Day-of-Year Hour Minute SYM/H`

## Output

- `output/stormlist.csv` — Storm parameter table (MPO, MIN, Ips, etc.)
- `output/images/*.png` — Per-storm plots (default)
- `output/images/allstorms.png` — Overview plot (`--all` mode)


## Makefile Targets

| Target | Command | Description |
|--------|---------|-------------|
| `download` | `make download START=240101 END=260101` | Download SYM-H data |
| `storm` | `make storm` | Run storm identification |
| `storm` | `make storm LLIMIT=120` | Run with custom llimit |
| `allplot` | `make allplot` | Generate overview plot |
| `clean` | `make clean` | Remove output files |

## Input Data Format

5 columns, space-separated: `Year Day Hour Minute SYM/H`

## Citations

If you use this tool, please cite:

1. Raj, J. K., Manu, V., Balan, N., Zhang, Q.-H., & Xing, Z.-Y. (2025). Capability of revised intensity and impulsive strength of geomagnetic storms and activities to identify severe space weather. *Space Weather*, 23, e2025SW004399. https://doi.org/10.1029/2025SW004399

2. Raj, J. K., Balan, N., Zhang, Q.-H., Otsuka, Y., Shiokawa, K., Xing, Z.-Y., et al. (2026). Relative contributions of solar wind dynamic pressure and interplanetary electric field on the early positive part of main phase of geomagnetic storms. *Space Weather*, 24, e2025SW004571. https://doi.org/10.1029/2025SW004571
