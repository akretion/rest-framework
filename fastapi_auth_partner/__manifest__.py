# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fastapi Auth Partner",
    "summary": """This provides an implementation of auth_partner for FastAPI""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": [
        "extendable_fastapi",
        "auth_partner",
    ],
    "data": [
        "security/res_group.xml",
        "security/ir.model.access.csv",
        "views/auth_partner_view.xml",
        "views/auth_directory_view.xml",
        "views/fastapi_endpoint_view.xml",
        "wizards/wizard_auth_partner_impersonate_view.xml",
    ],
    "demo": [
        "demo/auth_directory_demo.xml",
        "demo/fastapi_endpoint_demo.xml",
    ],
    "external_dependencies": {
        "python": ["itsdangerous"],
    },
}
