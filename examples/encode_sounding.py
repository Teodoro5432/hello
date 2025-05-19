#!/usr/bin/env python
"""Example script for encoding a vertical sounding into a BUFR file."""

import pandas as pd
from datetime import datetime
from bufr_encoder import BUFREncoder


def main():
    df = pd.DataFrame({
        'pressure_hPa': [1000, 850, 700, 500, 300, 200, 100, 50, 10],
        'temperature_C': [25.0, 15.0, 5.0, -15.0, -40.0, -55.0, -70.0, -70.0, -50.0],
        'dewpoint_C': [20.0, 10.0, 0.0, -20.0, -50.0, -65.0, -80.0, -80.0, -60.0],
        'windDirection': [180, 190, 210, 230, 250, 270, 290, 300, 310],
        'windSpeed': [5.0, 10.0, 15.0, 25.0, 35.0, 45.0, 55.0, 45.0, 25.0],
        'geopotentialHeight': [100, 1500, 3000, 5500, 9000, 11800, 16000, 20000, 31000]
    })
    metadata = {
        'stationNumber': 265,
        'blockNumber': 59,
        'latitude': 23.48,
        'longitude': 111.30,
        'year': datetime.now().year,
        'month': datetime.now().month,
        'day': datetime.now().day,
        'hour': 12,
        'minute': 0
    }
    encoder = BUFREncoder(template_name='TEMP')
    encoder.initialize_message()
    encoder.set_metadata(metadata)
    encoder.set_data(df)
    output_file = f'sounding_encoded_{datetime.now().strftime("%Y%m%d_%H%M%S")}.bufr'
    encoder.encode(output_file)
    print(f"BUFR file created: {output_file}")


if __name__ == "__main__":
    main()
