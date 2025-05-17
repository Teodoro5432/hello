from enso_tool.oni import ONIAnalyzer
from enso_tool.transition import TransitionAnalyzer
from enso_tool.visualization import ENSOVisualizer


def main():
    sst_file = './first_paper/datasets/era5_sst_1940_2024.nc'
    output_dir = './oni-analysis'
    start_year = 1940
    end_year = 2024

    oni_analyzer = ONIAnalyzer(sst_file, output_dir)
    oni_analyzer.load_sst_data()
    oni_analyzer.generate_climatology_periods(start_year, end_year)
    oni_analyzer.process_nino34_data()
    oni_analyzer.oni_ds = oni_analyzer.compute_oni()
    oni_analyzer.oni_df = oni_analyzer.oni_ds[['ONI']].to_dataframe().reset_index()
    oni_analyzer.oni_df = oni_analyzer.identify_enso_phases(oni_analyzer.oni_df)
    oni_analyzer.oni_df = oni_analyzer.number_sustained_events(oni_analyzer.oni_df)
    oni_analyzer.oni_df = oni_analyzer.categorize_events(oni_analyzer.oni_df)
    event_summary = oni_analyzer.summarize_events(oni_analyzer.oni_df)

    oni_analyzer.oni_df.to_csv(f'{output_dir}/oni_data.csv', index=False)
    event_summary.to_csv(f'{output_dir}/oni_events.csv', index=False)

    transition_analyzer = TransitionAnalyzer(sst_file, f'{output_dir}/oni_data.csv', output_dir)
    transition_analyzer.load_sst_data()
    transition_analyzer.load_oni_data()
    transition_analyzer.generate_climatology_periods(start_year, end_year)
    transition_analyzer.process_monthly_sst()
    transition_analyzer.calculate_monthly_anomalies()
    transition_analyzer.identify_enso_transitions()
    transition_analyzer.create_transition_datasets()
    transition_analyzer.calculate_composite_means()
    transition_analyzer.prepare_pacific_composites()

    visualizer = ENSOVisualizer(output_dir)
    visualizer.plot_oni_phases(oni_analyzer.oni_df, oni_analyzer.elnino_thresholds, end_date='2025-01-01')

    datasets = [
        transition_analyzer.pacific_sst_composites['very_strong_el_nino'],
        transition_analyzer.pacific_sst_composites['strong_el_nino'],
        transition_analyzer.pacific_sst_composites['moderate_el_nino'],
        transition_analyzer.pacific_sst_composites['weak_el_nino'],
        transition_analyzer.pacific_sst_composites['very_strong_la_nina'],
        transition_analyzer.pacific_sst_composites['strong_la_nina'],
        transition_analyzer.pacific_sst_composites['moderate_la_nina'],
        transition_analyzer.pacific_sst_composites['weak_la_nina'],
    ]

    plot_titles = [
        '(a) Very Strong El Niño', '(b) Strong El Niño',
        '(c) Moderate El Niño', '(d) Weak El Niño',
        '(e) Very Strong La Niña', '(f) Strong La Niña',
        '(g) Moderate La Niña', '(h) Weak La Niña',
    ]

    visualizer.create_longitude_time_plot(
        datasets=datasets,
        plot_titles=plot_titles,
        save_path=f'{output_dir}/lon_t_sst_plot'
    )

    print(f'Analysis complete! Results saved to {output_dir}')


if __name__ == '__main__':
    main()
