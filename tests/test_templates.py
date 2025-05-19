from bufr_encoder.templates.manager import TemplateManager


def test_get_template():
    manager = TemplateManager()
    template = manager.get_template('TEMP')
    assert 'descriptors' in template
    assert 'mapping' in template


def test_descriptor_mapping():
    manager = TemplateManager()
    mapping = manager.get_descriptor_mapping('TEMP')
    assert 'pressure' in mapping
