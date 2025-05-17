import os
import re
import xarray as xr
import pandas as pd
from pathlib import Path
import numpy as np


def extract_time_range(filename: str) -> tuple:
    """Extract start and end dates from filename.

    Example: tos_Omon_ACCESS-CM2_ssp585_r1i1p1f1_gn_201501-210012.nc
    Returns: ('2015-01', '2100-12')
    """
    match = re.search(r'(\d{6})-(\d{6})', filename)
    if not match:
        raise ValueError(f"Could not extract date range from filename: {filename}")

    start_date, end_date = match.groups()
    start = f"{start_date[:4]}-{start_date[4:]}"
    end = f"{end_date[:4]}-{end_date[4:]}"
    return start, end


def get_model_scenario_files(base_dir: str, model: str, scenario: str) -> list:
    """Get all NetCDF files for a specific model and scenario, sorted by start date."""
    model_dir = Path(base_dir) / model / scenario
    nc_files = list(model_dir.glob("*.nc"))

    target_start_year = 1930 if scenario.lower() == 'historical' else 2030
    target_end_year = 1999 if scenario.lower() == 'historical' else 2099

    filtered_files = []
    for file in nc_files:
        try:
            start_date_str, end_date_str = extract_time_range(file.name)
            file_start_year = int(start_date_str.split('-')[0])
            file_end_year = int(end_date_str.split('-')[0])
            if file_end_year >= target_start_year and file_start_year <= target_end_year:
                filtered_files.append(file)
        except ValueError:
            continue

    def get_start_date(file):
        start_date, _ = extract_time_range(file.name)
        return pd.to_datetime(start_date)

    return sorted(filtered_files, key=get_start_date)


def apply_spatial_filter(ds: xr.Dataset) -> xr.Dataset:
    """Filter dataset to latitudes between -5 and 5 degrees."""
    if 'latitude' in ds.coords:
        if len(ds.latitude.dims) == 1:
            ds = ds.sel(latitude=slice(-5, 5))
            if len(ds.latitude) == 0:
                return None
        elif len(ds.latitude.dims) == 2:
            if 'lat' in ds.dims:
                lat_indices = np.where((ds.lat >= -5) & (ds.lat <= 5))[0]
                if len(lat_indices) == 0:
                    return None
                ds = ds.isel(lat=lat_indices)
            else:
                y_dim, x_dim = ds.latitude.dims
                lat_mask = (ds.latitude >= -5) & (ds.latitude <= 5)
                y_indices = np.where(lat_mask.any(dim=x_dim))[0]
                if len(y_indices) == 0:
                    return None
                ds = ds.isel({y_dim: y_indices})
                ds.attrs['spatial_filter_note'] = (
                    "Dataset filtered to approximate latitude range -5° to 5°. "
                    "Due to curvilinear grid, some points outside this range may remain."
                )
    elif 'lat' in ds.coords:
        ds = ds.sel(lat=slice(-5, 5))
        if len(ds.lat) == 0:
            return None
    else:
        print("Warning: Could not identify latitude dimension")
    ds.attrs['spatial_filter'] = "Dataset filtered to latitude range -5° to 5°"
    return ds


def apply_temporal_filter(ds: xr.Dataset, scenario: str) -> xr.Dataset:
    """Filter dataset to target years depending on scenario."""
    time_values = ds.time.values
    if scenario.lower() == 'historical':
        time_indices = [i for i, t in enumerate(time_values) if t.year >= 1930 and t.year <= 1999]
    elif scenario.lower().startswith('ssp'):
        time_indices = [i for i, t in enumerate(time_values) if t.year >= 2030 and t.year <= 2099]
    else:
        time_indices = range(len(time_values))
    if not time_indices:
        return None
    filtered_ds = ds.isel(time=time_indices)
    filtered_ds.attrs['temporal_filter'] = (
        f"Dataset filtered to years {'1930-1999' if scenario.lower() == 'historical' else '2030-2099'}"
    )
    return filtered_ds


def extract_non_time_variables(ds: xr.Dataset) -> dict:
    """Return variables without time dimension."""
    non_time_vars = {}
    for var_name, var in ds.variables.items():
        if 'time' not in var.dims and var_name not in ds.coords:
            non_time_vars[var_name] = var
    return non_time_vars


def extract_data_for_time_range(file_paths: list, scenario: str) -> xr.Dataset:
    """Extract data from list of files for given time and spatial range."""
    datasets = []
    non_time_vars = None
    for file_path in file_paths:
        try:
            ds = xr.open_dataset(file_path, use_cftime=True)
            if non_time_vars is None:
                non_time_vars = extract_non_time_variables(ds)
            spatially_filtered_ds = apply_spatial_filter(ds)
            if spatially_filtered_ds is None:
                ds.close()
                continue
            temporally_filtered_ds = apply_temporal_filter(spatially_filtered_ds, scenario)
            if temporally_filtered_ds is None:
                ds.close()
                continue
            datasets.append(temporally_filtered_ds)
            ds.close()
        except Exception:
            continue
    if not datasets:
        return None
    template_ds = datasets[0].copy()
    time_vars_list = []
    for var_name in template_ds.data_vars:
        if 'time' in template_ds[var_name].dims:
            time_vars_dataset = xr.concat([ds[var_name] for ds in datasets], dim="time")
            time_vars_list.append(time_vars_dataset)
    combined_ds = xr.merge(time_vars_list)
    for var_name, var in template_ds.variables.items():
        if 'time' not in var.dims and var_name not in combined_ds.variables and var_name not in combined_ds.coords:
            combined_ds[var_name] = var
    combined_ds = combined_ds.sortby('time')
    for attr_name, attr_value in template_ds.attrs.items():
        combined_ds.attrs[attr_name] = attr_value
    if 'history' in combined_ds.attrs:
        combined_ds.attrs['history'] = f"Applied temporal and spatial filters on {pd.Timestamp.now()}; " + combined_ds.attrs['history']
    else:
        combined_ds.attrs['history'] = f"Applied temporal and spatial filters on {pd.Timestamp.now()}"
    return combined_ds


def check_processed_file_exists(output_dir: Path, model: str, scenario: str) -> bool:
    """Return True if processed file exists."""
    output_scenario_dir = output_dir / model / scenario
    if not output_scenario_dir.exists():
        return False
    existing_files = list(output_scenario_dir.glob("*.nc"))
    return len(existing_files) > 0


def main():
    input_base_dir = Path("CMIP6_downloaded_datasets")
    output_base_dir = Path("filtered_data")
    output_base_dir.mkdir(exist_ok=True)
    scenarios = ["historical", "ssp126", "ssp245", "ssp585"]
    model_dirs = [d for d in input_base_dir.iterdir() if d.is_dir()]
    for model_dir in model_dirs:
        model_name = model_dir.name
        for scenario in scenarios:
            if check_processed_file_exists(output_base_dir, model_name, scenario):
                continue
            scenario_dir = model_dir / scenario
            if not scenario_dir.exists():
                continue
            output_model_dir = output_base_dir / model_name
            output_model_dir.mkdir(exist_ok=True)
            output_scenario_dir = output_model_dir / scenario
            output_scenario_dir.mkdir(exist_ok=True)
            scenario_files = get_model_scenario_files(input_base_dir, model_name, scenario)
            if not scenario_files:
                continue
            extracted_data = extract_data_for_time_range(scenario_files, scenario)
            if extracted_data is None:
                continue
            var_name = None
            for var in extracted_data.data_vars:
                if 'time' in extracted_data[var].dims:
                    var_name = var
                    break
            if var_name is None:
                continue
            times = extracted_data.time.values
            start_time = times[0]
            end_time = times[-1]
            start_str = f"{start_time.year}{start_time.month:02d}"
            end_str = f"{end_time.year}{end_time.month:02d}"
            output_filename = f"{var_name}_Omon_{model_name}_{scenario}_r1i1p1f1_gn_eq5_{start_str}-{end_str}.nc"
            output_path = output_scenario_dir / output_filename
            extracted_data.to_netcdf(output_path)


if __name__ == "__main__":
    main()
