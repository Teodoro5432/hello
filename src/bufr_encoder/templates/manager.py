class TemplateManager:
    """Manages BUFR templates and descriptor sequences."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self):
        templates = {
            'TEMP': {
                'descriptors': [
                    '301001',
                    '301011',
                    '301013',
                    '307054',
                ],
                'mapping': {
                    'pressure': 'pressure',
                    'geopotentialHeight': 'nonCoordinateGeopotentialHeight',
                    'airTemperature': 'airTemperature',
                    'dewpointTemperature': 'dewpointTemperature',
                    'windDirection': 'windDirection',
                    'windSpeed': 'windSpeed',
                }
            }
        }
        return templates

    def get_template(self, template_name):
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        return self.templates[template_name]

    def get_descriptor_mapping(self, template_name):
        template = self.get_template(template_name)
        return template['mapping']
