import datetime
import numpy as np
import eccodes
from ..templates.manager import TemplateManager


def create_bufr_message(template_name, subtype=4):
    """Create a new BUFR message from a template."""
    bufr = eccodes.codes_bufr_new_from_sample("BUFR4")
    eccodes.codes_set(bufr, "masterTableNumber", 0)
    eccodes.codes_set(bufr, "bufrHeaderCentre", 98)
    eccodes.codes_set(bufr, "bufrHeaderSubCentre", 0)
    eccodes.codes_set(bufr, "updateSequenceNumber", 0)
    eccodes.codes_set(bufr, "dataCategory", 2)
    eccodes.codes_set(bufr, "internationalDataSubCategory", subtype)
    eccodes.codes_set(bufr, "dataSubCategory", 255)
    eccodes.codes_set(bufr, "masterTablesVersionNumber", 36)
    eccodes.codes_set(bufr, "localTablesVersionNumber", 0)
    eccodes.codes_set(bufr, "compressedData", 0)
    template_manager = TemplateManager()
    template = template_manager.get_template(template_name)
    descriptors = template['descriptors']
    descriptor_ints = []
    for desc in descriptors:
        if isinstance(desc, str):
            f = int(desc[0])
            x = int(desc[1:3])
            y = int(desc[3:6])
            descriptor_int = f * 100000 + x * 1000 + y
            descriptor_ints.append(descriptor_int)
        else:
            descriptor_ints.append(desc)
    eccodes.codes_set_array(bufr, "unexpandedDescriptors", descriptor_ints)
    return bufr


def create_sounding_message(data, metadata):
    """Create a BUFR message for a vertical sounding."""
    bufr = create_bufr_message("TEMP", subtype=4)
    now = datetime.datetime.now()
    eccodes.codes_set(bufr, "year", metadata.get('year', now.year))
    eccodes.codes_set(bufr, "month", metadata.get('month', now.month))
    eccodes.codes_set(bufr, "day", metadata.get('day', now.day))
    eccodes.codes_set(bufr, "hour", metadata.get('hour', now.hour))
    eccodes.codes_set(bufr, "minute", metadata.get('minute', now.minute))
    for key, bufr_key in {
        'stationNumber': 'stationNumber',
        'blockNumber': 'blockNumber',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'stationOrSiteName': 'stationOrSiteName'
    }.items():
        if key in metadata:
            try:
                value = metadata[key]
                if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                eccodes.codes_set(bufr, bufr_key, value)
            except Exception:
                pass
    num_levels = len(data)
    eccodes.codes_set(bufr, "numberOfSubsets", num_levels)
    for param, bufr_key in {
        'pressure': 'pressure',
        'airTemperature': 'airTemperature',
        'dewpointTemperature': 'dewpointTemperature',
        'windDirection': 'windDirection',
        'windSpeed': 'windSpeed',
        'geopotentialHeight': 'nonCoordinateGeopotentialHeight'
    }.items():
        if param in data.columns:
            values = data[param].values
            values = np.where(np.isnan(values), 9999, values)
            try:
                eccodes.codes_set_array(bufr, bufr_key, values)
            except Exception:
                pass
    return bufr
