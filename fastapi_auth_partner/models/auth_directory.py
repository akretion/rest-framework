# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AuthDirectory(models.Model):
    _inherit = "auth.directory"

    fastapi_endpoint_ids = fields.One2many(
        "fastapi.endpoint",
        "directory_id",
        string="FastAPI Endpoints",
    )

    cookie_secret_key = fields.Char(
        required=True,
        groups="base.group_system",
    )
    cookie_duration = fields.Integer(
        default=525600,
        help="In minute, default 525600 minutes => 1 year",
        required=True,
    )
    sliding_session = fields.Boolean()

    @property
    def _server_env_fields(self):
        return {"cookie_secret_key": {}}
