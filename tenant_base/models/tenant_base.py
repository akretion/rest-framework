# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _, fields


class TenantBase(models.AbstractModel):
    _name = 'tenant.base'
    _description = 'Tenant'

    _login_field = None
    _password_hash_field = None