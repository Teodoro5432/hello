import pandas as pd
from bufr_encoder.data.converters import convert_to_bufr_units


def test_convert_to_bufr_units():
    df = pd.DataFrame({'pressure_hPa': [1000], 'temperature_C': [20], 'dewpoint_C': [10]})
    converted = convert_to_bufr_units(df)
    assert 'pressure' in converted
    assert converted['pressure'][0] == 100000.0
    assert converted['airTemperature'][0] == 293.15
    assert converted['dewpointTemperature'][0] == 283.15
