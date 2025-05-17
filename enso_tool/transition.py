from typing import List, Dict
import pandas as pd
import numpy as np
import xarray as xr
from .base import ENSOBaseAnalyzer

class TransitionAnalyzer(ENSOBaseAnalyzer):
    """Analyze ENSO transitions and anomalies."""

    def __init__(self, sst_file: str, oni_file: str, output_dir: str = './output'):
        super().__init__(sst_file, output_dir)
        self.oni_file = oni_file
        self.oni_df: pd.DataFrame | None = None
        self.sst_monthly: xr.Dataset | None = None
        self.sst_anomalies: xr.Dataset | None = None
        self.transition_years: Dict[str, List[int]] | None = None
        self.transition_sst_ds: Dict[str, xr.Dataset] | None = None
        self.sst_composites: Dict[str, xr.DataArray] | None = None
        self.pacific_sst_composites: Dict[str, xr.Dataset] | None = None

    def load_oni_data(self) -> 'TransitionAnalyzer':
        self.oni_df = pd.read_csv(self.oni_file)
        self.oni_df['valid_time'] = pd.to_datetime(self.oni_df['valid_time'])
        return self

    def process_monthly_sst(self) -> None:
        sst_mean = self.sst_ds.mean(dim='latitude')
        times = pd.to_datetime(sst_mean.valid_time.values)
        monthly_times = pd.to_datetime(times).to_period('M').to_timestamp()
        sst_mean = sst_mean.assign_coords(valid_time=monthly_times)
        self.sst_monthly = sst_mean.groupby('valid_time').mean(dim='valid_time')
        self.sst_monthly = self.sst_monthly.assign_coords(valid_time=pd.to_datetime(self.sst_monthly.valid_time))

    def calculate_monthly_anomalies(self) -> 'TransitionAnalyzer':
        self.sst_anomalies = self._compute_anomalies(self.sst_monthly, 'sst')
        return self

    def _compute_anomalies(self, dataset: xr.Dataset, variable: str) -> xr.Dataset:
        anomaly_arrays = []
        for time in dataset.valid_time:
            timestamp = pd.to_datetime(time.values)
            year, month = timestamp.year, timestamp.month
            period = self.climatology_dict.get(year)
            if not period:
                anomaly_arrays.append(np.nan)
                continue
            start_year, end_year = period
            clim_slice = dataset[variable].sel(valid_time=slice(f'{start_year}-01-01', f'{end_year}-12-31'))
            month_data = clim_slice.sel(valid_time=clim_slice['valid_time'].dt.month == month)
            if month_data.size == 0:
                anomaly_arrays.append(np.nan)
                continue
            clim_mean = month_data.mean(dim='valid_time')
            time_value = dataset[variable].sel(valid_time=time)
            time_value, clim_mean = xr.align(time_value, clim_mean, join='exact')
            anomaly_arrays.append(time_value - clim_mean)
        return xr.concat(anomaly_arrays, dim='valid_time').to_dataset(name=variable)

    def identify_enso_transitions(self) -> Dict[str, List[int]]:
        phases = ['El Niño', 'La Niña']
        intensities = ['Very Strong', 'Strong', 'Moderate', 'Weak']
        transition_years: Dict[str, List[int]] = {}
        for phase in phases:
            for intensity in intensities:
                category = f"{intensity.lower().replace(' ', '_')}_{phase.lower().replace(' ', '_').replace('ñ', 'n')}"
                transition_years[category] = self._get_transition_years(phase, intensity)
        self.transition_years = transition_years
        return transition_years

    def _get_transition_years(self, phase: str, intensity: str) -> List[int]:
        df = self.oni_df.copy()
        df['prev_Phase'] = df['Phase'].shift(1)
        condition = (
            (df['Phase'] == phase) &
            (df['prev_Phase'].isin(['Neutral', 'La Niña' if phase == 'El Niño' else 'El Niño'])) &
            (df['Intensity'] == intensity)
        )
        return df.loc[condition, 'valid_time'].dt.year.tolist()

    def create_transition_datasets(self) -> 'TransitionAnalyzer':
        self.transition_sst_ds = {}
        for category, years in self.transition_years.items():
            if not years:
                continue
            self.transition_sst_ds[category] = self._create_24month_dataset(self.sst_anomalies, years, 'sst')
        return self

    def _create_24month_dataset(self, dataset: xr.Dataset, years: List[int], variable: str) -> xr.Dataset:
        longitude = dataset.longitude.values
        n_years = len(years)
        data_array = np.full((n_years, 24, len(longitude)), np.nan, dtype=np.float32)
        dates_array = np.full((n_years, 24), np.datetime64('NaT'), dtype='datetime64[ns]')
        valid_years = []
        for idx, year in enumerate(years):
            start_date = pd.Timestamp(year=year, month=1, day=1)
            end_date = pd.Timestamp(year=year+1, month=12, day=31)
            data_subset = dataset.sel(valid_time=slice(start_date, end_date))
            if len(data_subset.valid_time) == 0:
                continue
            n_months = min(24, len(data_subset.valid_time))
            data_array[idx, :n_months, :] = data_subset[variable].values[:n_months]
            dates = pd.date_range(start=start_date, periods=n_months, freq='MS')
            dates_array[idx, :n_months] = dates.values
            valid_years.append(year)
        if len(valid_years) < n_years:
            data_array = data_array[:len(valid_years), :, :]
            dates_array = dates_array[:len(valid_years), :]
        return xr.Dataset(
            {variable: (['transition_year', 'month', 'longitude'], data_array)},
            coords={
                'transition_year': valid_years,
                'month': np.arange(24),
                'longitude': longitude,
                'date': (['transition_year', 'month'], dates_array)
            }
        )

    def calculate_composite_means(self) -> 'TransitionAnalyzer':
        self.sst_composites = {}
        for category in self.transition_years.keys():
            if category in self.transition_sst_ds:
                self.sst_composites[category] = self.transition_sst_ds[category].sst.mean(dim='transition_year', skipna=True)
        return self

    def spatial_slice_pacific(self, dataarray: xr.DataArray, variable: str) -> xr.Dataset:
        if isinstance(dataarray, xr.Dataset):
            dataarray = dataarray[variable]
        west_pacific = dataarray.sel(longitude=slice(120, 180))
        east_pacific = dataarray.sel(longitude=slice(-180, -80))
        pacific = xr.concat([west_pacific, east_pacific], dim='longitude')
        num_longitudes = pacific.sizes['longitude']
        idx = np.arange(num_longitudes)
        pacific = pacific.assign_coords(custom_longitude=('longitude', idx), number=('longitude', idx))
        if 'month' in pacific.dims:
            pacific = pacific.rename({'month': 'rolling_time'})
        pacific['rolling_time'] = pacific['rolling_time'].astype('int64')
        pacific['number'] = pacific['number'].astype('int64')
        pacific['custom_longitude'] = pacific['custom_longitude'].astype('int64')
        return pacific.transpose('rolling_time', 'longitude').to_dataset(name=variable)

    def prepare_pacific_composites(self) -> 'TransitionAnalyzer':
        self.pacific_sst_composites = {}
        for category in self.transition_years.keys():
            if category in self.sst_composites:
                self.pacific_sst_composites[category] = self.spatial_slice_pacific(self.sst_composites[category], 'sst')
        return self
