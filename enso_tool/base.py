import os
from typing import Dict, Tuple
import xarray as xr

class ENSOBaseAnalyzer:
    """Base class for ENSO data processing and utilities."""

    def __init__(self, sst_file: str, output_dir: str = './output'):
        self.sst_file = sst_file
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.sst_ds = None
        self.climatology_dict: Dict[int, Tuple[int, int]] | None = None

    def load_sst_data(self) -> 'ENSOBaseAnalyzer':
        """Load SST dataset."""
        self.sst_ds = xr.open_dataset(self.sst_file).astype('float64')
        return self

    def generate_climatology_periods(self, start_year: int, end_year: int) -> Dict[int, Tuple[int, int]]:
        """Generate climatology windows for each year."""
        if end_year - start_year + 1 < 31:
            raise ValueError("Range must be at least 31 years to accommodate climatology windows.")
        climatology_dict: Dict[int, Tuple[int, int]] = {}
        fixed_start_climatology = self._calculate_climatology_window(start_year + 15)
        fixed_end_climatology = self._calculate_climatology_window(end_year - 15)
        for year in range(start_year, end_year + 1):
            if start_year + 15 <= year <= end_year - 15:
                climatology_dict[year] = self._calculate_climatology_window(year)
            elif year < start_year + 15:
                climatology_dict[year] = fixed_start_climatology
            else:
                climatology_dict[year] = fixed_end_climatology
        self.climatology_dict = climatology_dict
        return climatology_dict

    @staticmethod
    def _calculate_climatology_window(year: int) -> Tuple[int, int]:
        """Calculate 30-year climatology window for a given year."""
        rounded_year = (year // 5) * 5
        start_year = rounded_year - 14
        end_year = rounded_year + 15
        return start_year, end_year
