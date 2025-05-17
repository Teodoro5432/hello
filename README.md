# hello
hello world

## Spatiotemporal Filter for CMIP6

This repository includes a script `spatiotemporal_filter.py` that processes CMIP6 NetCDF datasets. The script applies latitude and time filtering to prepare the data for the existing pipeline, which previously only handled ERA5 files.

To run the filter over a directory named `CMIP6_downloaded_datasets` and store results in `filtered_data`:

```bash
python spatiotemporal_filter.py
```

The script detects model and scenario directories, extracts the relevant time range, filters latitude to ±5°, and saves consolidated files under `filtered_data/<model>/<scenario>/`.
