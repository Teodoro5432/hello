#!/usr/bin/env python
"""Example encoding BUFR from CSV."""

import pandas as pd
from bufr_encoder import BUFREncoder
from bufr_encoder.data.ingestion import load_from_csv


def main(csv_file):
    df = load_from_csv(csv_file)
    encoder = BUFREncoder(template_name='TEMP')
    encoder.initialize_message()
    encoder.set_data(df)
    encoder.encode('output.bufr')
    print('Encoded output.bufr')


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
