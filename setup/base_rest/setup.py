import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'accept_language': 'parse-accept-language',
                'marshmallow-objects': "marshmallow-objects>=2.0.0"
            },
        },
    }
)
