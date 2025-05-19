import pandas as pd

def convert_to_bufr_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert values from standard units to BUFR units."""
    df_converted = df.copy()
    if 'temperature_C' in df.columns:
        df_converted['airTemperature'] = df['temperature_C'] + 273.15
    if 'dewpoint_C' in df.columns:
        df_converted['dewpointTemperature'] = df['dewpoint_C'] + 273.15
    if 'pressure_hPa' in df.columns:
        df_converted['pressure'] = df['pressure_hPa'] * 100.0
    if 'geopotentialHeight' in df.columns:
        df_converted['nonCoordinateGeopotentialHeight'] = df['geopotentialHeight']
    if 'windDirection' in df.columns:
        df_converted['windDirection'] = df['windDirection']
    if 'windSpeed' in df.columns:
        df_converted['windSpeed'] = df['windSpeed']
    return df_converted
