import os
from typing import List
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.dates as mdates
from matplotlib.dates import YearLocator, DateFormatter
from datetime import datetime
import scipy.ndimage as ndi
from .oni import ENSOThresholds

class ENSOVisualizer:
    """Handle visualization of ENSO data."""

    def __init__(self, output_dir: str = './output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.plot_params = {
            'colorbar_label': 'SST Anomaly (°C)',
            'cmap': 'RdBu_r',
            'contour_levels': [i * 0.25 for i in range(-15, 15)],
            'contour_fmt': lambda x: f"{x:.2f}".rstrip('0').rstrip('.'),
            'fontsize_title': 20,
            'fontsize_ylabel': 22,
            'fontsize_tick': 20,
            'fontsize_clabel': 22,
        }

    def plot_oni_phases(self, df: pd.DataFrame, thresholds: ENSOThresholds, end_date: str | None = None) -> None:
        plot_df = df.copy()
        if end_date:
            plot_df = plot_df[plot_df['valid_time'] <= pd.Timestamp(end_date)]
        fig, ax = plt.subplots(figsize=(15, 5))
        ax.plot(plot_df['valid_time'], plot_df['ONI'], color='black')
        ax.fill_between(plot_df['valid_time'], 0.5, plot_df['ONI'], where=(plot_df['Phase'] == 'El Niño'), color='red', alpha=0.5, interpolate=True)
        ax.fill_between(plot_df['valid_time'], plot_df['ONI'], -0.5, where=(plot_df['Phase'] == 'La Niña'), color='blue', alpha=0.5, interpolate=True)
        thresholds_dict = {
            'Very Strong': thresholds.very_strong,
            'Strong': thresholds.strong,
            'Moderate': thresholds.moderate,
            'Weak': thresholds.weak,
        }
        for value in thresholds_dict.values():
            ax.axhline(value, color='gray', linewidth=1, linestyle='--')
            ax.axhline(-value, color='gray', linewidth=1, linestyle='--')
        ax.axhline(0, color='black', linewidth=0.5)
        label_offset = 1.01
        label_size = 14
        for label, value in thresholds_dict.items():
            ax.text(label_offset, value + 0.25, label, ha='left', va='center', transform=ax.get_yaxis_transform(), color='red', fontsize=label_size)
            ax.text(label_offset, -value - 0.25, label, ha='left', va='center', transform=ax.get_yaxis_transform(), color='blue', fontsize=label_size)
        ax.set_xlabel('Year', fontsize=16)
        ax.set_ylabel('ONI (°C)', fontsize=16)
        tick_params = {'labelsize': 14, 'length': 10, 'width': 2, 'direction': 'inout', 'pad': 10}
        ax.tick_params(axis='x', which='major', **tick_params)
        ax.tick_params(axis='y', which='major', **tick_params)
        ax.tick_params(axis='x', which='minor', labelsize=14, length=5, width=1, direction='inout', pad=10)
        ax.set_xlim(plot_df['valid_time'].min(), plot_df['valid_time'].max())
        ax.set_ylim(-3, 3)
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        ax.margins(x=0)
        major_locator = YearLocator(5)
        minor_locator = YearLocator(1)
        date_formatter = DateFormatter('%Y')
        ax.xaxis.set_major_locator(major_locator)
        ax.xaxis.set_minor_locator(minor_locator)
        ax.xaxis.set_major_formatter(date_formatter)
        start_year = plot_df['valid_time'].min().year
        end_year = plot_df['valid_time'].max().year
        extra_dates = [datetime(year, 1, 1) for year in [start_year, end_year]]
        extra_ticks_mpl = [mdates.date2num(date) for date in extra_dates]
        existing_ticks = ax.get_xticks()
        combined_ticks = sorted(set(existing_ticks.tolist() + extra_ticks_mpl))
        filtered_ticks = [tick for tick in combined_ticks if mdates.num2date(tick).year != 2025]
        ax.set_xticks(filtered_ticks)
        plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
        fig.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.20)
        plot_path = os.path.join(self.output_dir, 'oni_phases')
        plt.savefig(f"{plot_path}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{plot_path}.eps", format='eps', dpi=300, bbox_inches='tight')
        plt.close()

    def create_longitude_time_plot(self, datasets: List[xr.Dataset], plot_titles: List[str], save_path: str, vmin: float = -2, vmax: float = 2) -> None:
        if len(datasets) != 8 or len(plot_titles) != 8:
            raise ValueError('Must provide exactly 8 datasets and 8 titles')
        fig, axes = plt.subplots(2, 4, figsize=(20, 12), constrained_layout=True)
        for row in range(2):
            for col in range(4):
                idx = row * 4 + col
                ds = datasets[idx]
                title = plot_titles[idx]
                ax = axes[row, col]
                data = ds['sst'].values
                rolling_time = ds['rolling_time'].values
                custom_longitude = ds['custom_longitude'].values
                lon_grid, time_grid = np.meshgrid(custom_longitude, rolling_time)
                sigma = (3, 6)
                data_smooth = ndi.gaussian_filter(data, sigma=sigma)
                img = ax.pcolormesh(lon_grid, time_grid, data_smooth, cmap=self.plot_params['cmap'], vmin=vmin, vmax=vmax, shading='auto')
                contours = ax.contour(lon_grid, time_grid, data_smooth, levels=self.plot_params['contour_levels'], colors='white', linewidths=1.5)
                labels = ax.clabel(contours, inline=True, fontsize=self.plot_params['fontsize_clabel'], fmt=self.plot_params['contour_fmt'])
                for label in labels:
                    label.set_rotation(0)
                    label.set_color('black')
                ax.set_title(title, fontsize=self.plot_params['fontsize_title'], pad=15, color='black')
                if col == 0:
                    ax.set_ylabel('Year [0]               Year [+1]', fontsize=self.plot_params['fontsize_ylabel'], labelpad=10, color='black')
                ax.tick_params(axis='both', which='major', labelsize=self.plot_params['fontsize_tick'], labelcolor='black')
                x_ticks = [0, (60/160)*640, (120/160)*640, 640]
                x_labels = ['120°E', '180°', '120°W', '80°W']
                ax.set_xticks(x_ticks)
                ax.set_xticklabels(x_labels, color='black', fontsize=self.plot_params['fontsize_tick'])
                y_ticks = [-0.5, 2.5, 5.5, 8.5, 11.5, 14.5, 17.5, 20.5, 23.5]
                y_labels = ['JAN', 'APR', 'JUL', 'OCT', 'JAN', 'APR', 'JUL', 'OCT', 'JAN']
                ax.set_yticks(y_ticks)
                ax.set_yticklabels(y_labels, color='black', fontsize=self.plot_params['fontsize_tick'])
                for spine in ax.spines.values():
                    spine.set_linewidth(3)
                    spine.set_color('black')
                ax.axhline(y=11.5, linestyle='--', color='black')
                for x_pos in [(60/160)*640, (120/160)*640]:
                    ax.plot(x_pos, -0.25, marker='v', markersize=3, markeredgecolor='black', markerfacecolor='black')
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        sm = plt.cm.ScalarMappable(cmap=self.plot_params['cmap'], norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), orientation='horizontal', fraction=0.046, pad=0.04, aspect=30, shrink=0.6)
        cbar.set_label(self.plot_params['colorbar_label'], fontsize=self.plot_params['fontsize_ylabel'], labelpad=5, color='black')
        cbar.ax.tick_params(labelsize=self.plot_params['fontsize_tick'], labelcolor='black')
        for spine in cbar.ax.spines.values():
            spine.set_linewidth(3)
            spine.set_color('black')
        plt.savefig(f"{save_path}.png", dpi=300)
        plt.savefig(f"{save_path}.eps", dpi=300, format='eps')
        plt.close()
