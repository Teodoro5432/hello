# ENSO Analysis Tools

This repository contains utilities to analyze ENSO (El Niño Southern Oscillation)
using sea surface temperature data. The code is divided into a small Python
package located in `enso_tool` and a sample script `run_analysis.py` showing how
it can be used.

The modules include:

- `base.py` – shared utilities and dataset loading
- `oni.py` – Oceanic Niño Index processing
- `transition.py` – analysis of ENSO transitions
- `visualization.py` – helper functions for plots

To execute the full analysis workflow run:

```bash
python run_analysis.py
```

The script expects the ERA5 SST dataset at
`./first_paper/datasets/era5_sst_1940_2024.nc` and will generate output in the
`./oni-analysis` directory.
