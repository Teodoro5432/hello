import pandas as pd
import io


def load_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Load data from a pandas DataFrame."""
    normalized_df = df.copy()
    required_columns = ['pressure', 'airTemperature', 'dewpointTemperature',
                       'windDirection', 'windSpeed']
    alt_names = {
        'pressure': ['pressure_hPa', 'pressure'],
        'airTemperature': ['airTemperature', 'temperature', 'temperature_C'],
        'dewpointTemperature': ['dewpointTemperature', 'dewPointTemperature', 'dewpoint_C'],
        'windDirection': ['windDirection'],
        'windSpeed': ['windSpeed']
    }
    for col in required_columns:
        found = False
        for alt in alt_names.get(col, []):
            if alt in normalized_df.columns:
                if alt != col:
                    normalized_df[col] = normalized_df[alt]
                found = True
                break
        if not found:
            normalized_df[col] = float('nan')
    return normalized_df


def load_from_csv(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    return load_from_dataframe(df)


def load_from_decoder_output(text_file: str):
    metadata = {}
    data_lines = []
    in_metadata = False
    in_profile = False
    with open(text_file, 'r') as f:
        for line in f:
            if 'Station Information:' in line:
                in_metadata = True
                continue
            if in_metadata and ':' in line:
                key, value = line.strip().split(':', 1)
                metadata[key.strip()] = value.strip()
            if 'Vertical Profile (ALL Pressure Levels):' in line:
                in_metadata = False
                in_profile = True
                continue
            if in_profile and line.strip() and not line.startswith('Total levels:'):
                data_lines.append(line.strip())
    df = pd.read_csv(io.StringIO('\n'.join(data_lines)), sep='\s+')
    return {'metadata': metadata, 'data': df}
