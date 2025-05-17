from dataclasses import dataclass
from typing import Dict
import pandas as pd
import numpy as np
import xarray as xr
from .base import ENSOBaseAnalyzer

@dataclass
class ENSOThresholds:
    """Data class for ENSO threshold definitions."""
    very_strong: float = 2.0
    strong: float = 1.5
    moderate: float = 1.0
    weak: float = 0.5

class ONIAnalyzer(ENSOBaseAnalyzer):
    """Analyze Oceanic Niño Index (ONI) data."""

    def __init__(self, sst_file: str, output_dir: str = './output'):
        super().__init__(sst_file, output_dir)
        self.elnino_thresholds = ENSOThresholds()
        self.lanina_thresholds = ENSOThresholds()
        self.oni_ds: xr.Dataset | None = None
        self.oni_df: pd.DataFrame | None = None

    def process_nino34_data(self) -> None:
        sst_nino34 = self.sst_ds['sst'].sel(latitude=slice(5, -5), longitude=slice(-170, -120))
        sst_nino34_mean = sst_nino34.mean(('latitude', 'longitude')).to_dataframe()
        sst_monthly = sst_nino34_mean['sst'].resample('M').mean()
        sst_monthly.index = sst_monthly.index.to_period('M').to_timestamp()
        sst_monthly = sst_monthly.reset_index()
        self.sst_nino34_mean_rol3m = (
            pd.DataFrame({
                'valid_time': sst_monthly['valid_time'],
                'sst': sst_monthly['sst'].rolling(window=3, center=True).mean()
            })
            .dropna()
            .set_index('valid_time')
            .to_xarray()
        )

    def compute_oni(self) -> xr.Dataset:
        sst = self.sst_nino34_mean_rol3m['sst']
        valid_times = self.sst_nino34_mean_rol3m['valid_time']
        sst_clim_avg = []
        for time in valid_times:
            timestamp = pd.to_datetime(time.values)
            year, month = timestamp.year, timestamp.month
            period = self.climatology_dict.get(year)
            if not period:
                sst_clim_avg.append(np.nan)
                continue
            start_year, end_year = period
            climatology_slice = sst.sel(valid_time=slice(f'{start_year}-01-01', f'{end_year}-12-31'))
            climatology_month = climatology_slice.sel(valid_time=climatology_slice['valid_time'].dt.month == month)
            if climatology_month.size == 0:
                sst_clim_avg.append(np.nan)
                continue
            mean_sst = climatology_month.mean().item()
            sst_clim_avg.append(mean_sst)
        dataset = self.sst_nino34_mean_rol3m.assign(sst_clim_avg=('valid_time', sst_clim_avg))
        dataset = dataset.assign(ONI=dataset['sst'] - dataset['sst_clim_avg'])
        return dataset

    def identify_enso_phases(self, df: pd.DataFrame) -> pd.DataFrame:
        df['Phase'] = 'Neutral'
        for i in range(len(df) - 4):
            oni_values = df['ONI'].iloc[i:i+5]
            if (oni_values >= 0.5).all():
                df.loc[df.index[i:i+5], 'Phase'] = 'El Niño'
            elif (oni_values <= -0.5).all():
                df.loc[df.index[i:i+5], 'Phase'] = 'La Niña'
        return df

    def number_sustained_events(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ['ElNino_event', 'LaNina_event', 'Neutral_event']:
            df[col] = pd.Series(dtype='Int64')
        event_counters = {'El Niño': 0, 'La Niña': 0, 'Neutral': 0}
        current_phase = None
        for idx, row in df.iterrows():
            phase = row['Phase']
            if phase != current_phase:
                if phase in event_counters:
                    event_counters[phase] += 1
                current_phase = phase
            if phase == 'El Niño':
                df.at[idx, 'ElNino_event'] = event_counters[phase]
            elif phase == 'La Niña':
                df.at[idx, 'LaNina_event'] = event_counters[phase]
            elif phase == 'Neutral':
                df.at[idx, 'Neutral_event'] = event_counters[phase]
        return df

    def categorize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        categories: Dict[float, str] = {2.0: 'Very Strong', 1.5: 'Strong', 1.0: 'Moderate', 0.5: 'Weak'}
        def get_intensity(oni_values: np.ndarray, phase: str) -> str:
            thresholds = sorted(categories.keys(), reverse=True)
            for threshold in thresholds:
                condition = oni_values >= threshold if phase == 'El Niño' else oni_values <= -threshold
                condition_int = condition.astype(int)
                rolling_sum = pd.Series(condition_int).rolling(window=3, min_periods=3).sum()
                if (rolling_sum >= 3).any():
                    return categories[threshold]
            return 'Weak'
        for event_num in df['ElNino_event'].dropna().unique():
            event_mask = df['ElNino_event'] == event_num
            oni_values = df.loc[event_mask, 'ONI'].values
            intensity = get_intensity(oni_values, 'El Niño')
            df.loc[event_mask, 'Intensity'] = intensity
        for event_num in df['LaNina_event'].dropna().unique():
            event_mask = df['LaNina_event'] == event_num
            oni_values = df.loc[event_mask, 'ONI'].values
            intensity = get_intensity(oni_values, 'La Niña')
            df.loc[event_mask, 'Intensity'] = intensity
        df.loc[df['Phase'] == 'Neutral', 'Intensity'] = ''
        return df

    def summarize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        df_filtered = df[df['Phase'].isin(['El Niño', 'La Niña'])].copy()
        df_filtered = df_filtered.sort_values('valid_time').reset_index(drop=True)
        events = []
        current_event = None
        for _, row in df_filtered.iterrows():
            phase = row['Phase']
            intensity = row['Intensity']
            date = row['valid_time']
            if current_event is None:
                current_event = {'start_date': date, 'end_date': date, 'phase': phase, 'intensity': intensity}
            else:
                expected_next_date = current_event['end_date'] + pd.DateOffset(months=1)
                same_event = (
                    date == expected_next_date and phase == current_event['phase'] and intensity == current_event['intensity']
                )
                if same_event:
                    current_event['end_date'] = date
                else:
                    events.append(current_event)
                    current_event = {'start_date': date, 'end_date': date, 'phase': phase, 'intensity': intensity}
        if current_event:
            events.append(current_event)
        summary_df = pd.DataFrame(events)
        summary_df['Period'] = list(zip(
            summary_df['start_date'].dt.strftime('%Y-%m-%d'),
            summary_df['end_date'].dt.strftime('%Y-%m-%d')
        ))
        return summary_df[['Period', 'phase', 'intensity']].rename(columns={'phase': 'Phase', 'intensity': 'Intensity'})
