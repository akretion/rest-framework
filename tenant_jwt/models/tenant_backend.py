# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import hmac
import json
from hashlib import sha256

from base64 import urlsafe_b64encode
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.connector_tenant_base.models.tenant_backend_base import TenantBackendBase

class TenantBackendBase(TenantBackendBase):
    _inherit = "tenant.backend.base"
    _description = "Tenant Backend"

    jwt_secret_key = fields.Char()

    def sign_in(self, login, password):
        pwd_hash = sha256(password)
        tenant = self.env[tenant_model].sign_in(login, pwd_hash)
        if tenant:
            return tenant
        raise ValidationError(_("Tenant credentials invalid"))

    def sign_up(self, login, password):
        pwd_hash = sha256(password)
        return self.env[tenant_model].sign_up(login, pwd_hash, self.id)

    def reset_password(self, tenant):
        setattr(tenant, tenant._password_hash_field, "")


    def _jwt_get_signature(self, header, payload):
        to_hash = "{}.{}".format(header, payload)
        return hmac.digest(self.jwt_secret_token, to_hash, "sha256")

    def jwt_verify_validity(self, token):
        split = token.split(".")
        if len(split) != 3:
            raise ValidationError(_("Bad JWT token: incorrect parts lengths"))
        signature = self._get_signature(split[0], split[1])
        if signature != split[2]:
            raise ValidationError(_("Bad JWT token: could not verify signature"))
        return True

    def jwt_generate(self, tenant):
        backend = "{}{}".format(self._name, self.id)
        login = getattr(tenant, tenant._login_field)
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"backend": backend, "login": login}
        header_encoded = urlsafe_b64encode(json.dumps(header))
        payload_encoded = urlsafe_b64encode(json.dumps(payload))
        signature = self._jwt_get_signature(header_encoded, payload_encoded)
        token = "{}.{}.{}".format(header_encoded, payload_encoded, signature)
        return token
