import pandas as pd
import eccodes
from .bufr_sections import create_sounding_message
from ..templates.manager import TemplateManager
from ..data.converters import convert_to_bufr_units


class BUFREncoder:
    """Main BUFR Encoder class that manages the encoding process."""

    def __init__(self, template_name='TEMP', edition=4):
        """Initialize a new BUFR encoder instance."""
        self.template_name = template_name
        self.edition = edition
        self.bufr_handle = None
        self.template_manager = TemplateManager()

    def initialize_message(self):
        """Initialize a new BUFR message from template."""
        self.bufr_handle = create_sounding_message(pd.DataFrame(), {})
        eccodes.codes_set(self.bufr_handle, 'edition', self.edition)
        return self

    def set_metadata(self, metadata):
        """Set BUFR message metadata."""
        if self.bufr_handle is None:
            raise RuntimeError("BUFR message not initialized")
        for key, value in metadata.items():
            eccodes.codes_set(self.bufr_handle, key, value)
        return self

    def _convert_to_bufr_units(self, df):
        return convert_to_bufr_units(df)

    def set_data(self, data_frame):
        """Set the data section content from a DataFrame."""
        if self.bufr_handle is None:
            raise RuntimeError("BUFR message not initialized")
        df_bufr = self._convert_to_bufr_units(data_frame)
        descriptor_mapping = self.template_manager.get_descriptor_mapping(self.template_name)
        for column in df_bufr.columns:
            if column in descriptor_mapping:
                bufr_key = descriptor_mapping[column]
                eccodes.codes_set_array(self.bufr_handle, bufr_key, df_bufr[column].values)
        return self

    def encode(self, output_file):
        """Encode the BUFR message and write to file."""
        if self.bufr_handle is None:
            raise RuntimeError("BUFR message not initialized")
        eccodes.codes_set(self.bufr_handle, 'pack', 1)
        with open(output_file, 'wb') as f:
            eccodes.codes_write(self.bufr_handle, f)
        eccodes.codes_release(self.bufr_handle)
        self.bufr_handle = None
