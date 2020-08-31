# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import uuid
from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent


class RestTenantBase(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "rest.tenant.base"
    _usage = "tenant"
    _tenant_backend = None
    _tenant = None

    def _sign_up(self, login, password):
        return self.env[self._tenant_backend].sign_up(login, password)

    def _sign_in(self, login, password):
        return self.env[self._tenant_backend].sign_in(login, password)

    def _sign_out(self, tenant_identifier):
        return self.env[self._tenant_backend].sign_out(tenant_identifier)

    def _change_password(self, password, tenant_identifier):
        return self.env[self._tenant_backend].change_password(password, tenant_identifier)

    def _reset_password(self, tenant_identifier):
        return self.env[self._tenant_backend].reset_password(tenant_identifier)
