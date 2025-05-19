#!/usr/bin/env python
"""Example round-trip encoding/decoding test."""

import pandas as pd
import eccodes
from bufr_encoder import BUFREncoder


def main():
    df = pd.read_csv('../tests/data/sample_sounding.csv')
    encoder = BUFREncoder(template_name='TEMP')
    encoder.initialize_message()
    encoder.set_data(df)
    encoder.encode('temp.bufr')
    with open('temp.bufr', 'rb') as f:
        bufr = eccodes.codes_bufr_new_from_file(f)
        eccodes.codes_set(bufr, 'unpack', 1)
        pressure = eccodes.codes_get_array(bufr, 'pressure')
        print('Decoded levels:', len(pressure))
        eccodes.codes_release(bufr)


if __name__ == '__main__':
    main()
