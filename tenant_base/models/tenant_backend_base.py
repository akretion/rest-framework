# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import hmac
import json
from hashlib import sha256

from base64 import urlsafe_b64encode
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class TenantBackendBase(models.AbstractModel):
    _name = "tenant.backend.base"
    _description = "Tenant Backend"
    _tenant_model = None  # ex: ShopinvaderTenantBackend

    def sign_in(self, login, password):
        pwd_hash = sha256(password)
        tenant = self.env[self._tenant_model].sign_in(login, pwd_hash)
        if tenant:
            return tenant
        raise ValidationError(_("Tenant credentials invalid"))

    def sign_in(self, login, pwd_hash):
        tenant = self.search([
            (self._login_field, '=', login),
            (self._password_hash_field, '=', pwd_hash)
        ])
        return tenant

    def sign_up(self, login, password):
        pwd_hash = sha256(password)
        tenant = self.env[self._tenant_model]
        pwd_hash_field = tenant._password_hash_field
        login_field = tenant._login_field
        already_exists = tenant.search([
            (login_field, '=', login)
        ])

        return self.env[self._tenant_model].sign_up(login, pwd_hash, self.id)

    def sign_up(self, login, pwd_hash, backend_id):
        if already_exists:
            raise ValidationError(_("Username already exists"))
        else:
            new_tenant = self.create({
                self._login_field: login,
                self._password_hash_field: pwd_hash,
            })
        return new_tenant


    def reset_password(self, tenant):
        setattr(tenant, tenant._password_hash_field, "")
