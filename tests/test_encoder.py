import os
import pandas as pd
import numpy as np
import eccodes
from bufr_encoder import BUFREncoder
from bufr_encoder.data.converters import convert_to_bufr_units


def test_unit_conversion():
    df = pd.DataFrame({
        'pressure_hPa': [1000, 500, 100],
        'temperature_C': [20, 0, -50],
        'dewpoint_C': [15, -10, -60]
    })
    converted = convert_to_bufr_units(df)
    assert converted['pressure'][0] == 100000.0
    assert converted['airTemperature'][0] == 293.15
    assert converted['dewpointTemperature'][0] == 288.15


def test_encoder_initialization():
    encoder = BUFREncoder(template_name='TEMP')
    assert encoder.template_name == 'TEMP'
    assert encoder.edition == 4
    assert encoder.bufr_handle is None


def test_round_trip_encoding(tmp_path):
    df = pd.DataFrame({
        'pressure_hPa': [1000, 850, 700],
        'temperature_C': [25.0, 15.0, 5.0],
        'dewpoint_C': [20.0, 10.0, 0.0],
        'windDirection': [180, 190, 210],
        'windSpeed': [5.0, 10.0, 15.0],
        'geopotentialHeight': [100, 1500, 3000]
    })
    metadata = {
        'stationNumber': 265,
        'blockNumber': 59,
        'latitude': 23.48,
        'longitude': 111.30,
        'year': 2023,
        'month': 5,
        'day': 15,
        'hour': 12,
        'minute': 0
    }
    output_file = tmp_path / 'test_sounding.bufr'
    encoder = BUFREncoder(template_name='TEMP')
    encoder.initialize_message()
    encoder.set_metadata(metadata)
    encoder.set_data(df)
    encoder.encode(str(output_file))
    assert os.path.exists(output_file)
    with open(output_file, 'rb') as f:
        bufr = eccodes.codes_bufr_new_from_file(f)
        assert bufr is not None
        eccodes.codes_set(bufr, 'unpack', 1)
        assert eccodes.codes_get(bufr, 'dataCategory') == 2
        assert eccodes.codes_get(bufr, 'stationNumber') == metadata['stationNumber']
        pressure = eccodes.codes_get_array(bufr, 'pressure')
        assert len(pressure) == len(df)
        pressure_hpa = pressure / 100.0
        np.testing.assert_allclose(pressure_hpa, df['pressure_hPa'], rtol=1e-5)
        eccodes.codes_release(bufr)
