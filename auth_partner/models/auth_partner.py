# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta

import passlib

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, UserError

from odoo.addons.auth_signup.models.res_partner import random_token

# please read passlib great documentation
# https://passlib.readthedocs.io
# https://passlib.readthedocs.io/en/stable/narr/quickstart.html#choosing-a-hash
# be carefull odoo requirements use an old version of passlib
# TODO: replace with a JWT token
DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(["pbkdf2_sha512"])
DEFAULT_CRYPT_CONTEXT_TOKEN = passlib.context.CryptContext(
    ["pbkdf2_sha512"], pbkdf2_sha512__salt_size=0
)


_logger = logging.getLogger(__name__)


class AuthPartner(models.Model):
    _name = "auth.partner"
    _description = "Auth Partner"
    _rec_name = "login"

    partner_id = fields.Many2one(
        "res.partner", "Partner", required=True, ondelete="cascade", index=True
    )
    directory_id = fields.Many2one(
        "auth.directory", "Directory", required=True, index=True
    )
    user_can_impersonate = fields.Boolean(
        compute="_compute_user_can_impersonate",
        help="Technical field to check if the user can impersonate",
    )
    impersonating_user_ids = fields.Many2many(
        related="directory_id.impersonating_user_ids",
    )
    login = fields.Char(compute="_compute_login", store=True, required=True, index=True)
    password = fields.Char(compute="_compute_password", inverse="_inverse_password")
    encrypted_password = fields.Char(index=True)
    token_set_password_encrypted = fields.Char()
    token_expiration = fields.Datetime()
    token_impersonating_encrypted = fields.Char()
    token_impersonating_expiration = fields.Datetime()
    nbr_pending_reset_sent = fields.Integer(
        index=True,
        help=(
            "Number of pending reset sent from your customer."
            "This field is usefull when after a migration from an other system "
            "you ask all you customer to reset their password and you send"
            "different mail depending on the number of reminder"
        ),
    )
    date_last_request_reset_pwd = fields.Datetime(
        help="Date of the last password reset request"
    )
    date_last_sucessfull_reset_pwd = fields.Datetime(
        help="Date of the last sucessfull password reset"
    )

    token_mail_validation_encrypted = fields.Char()
    mail_verified = fields.Boolean(
        help="This field is set to True when the user has clicked on the link sent by email"
    )

    _sql_constraints = [
        (
            "directory_login_uniq",
            "unique (directory_id, login)",
            "Login must be uniq per directory !",
        ),
    ]

    # hack to solve sql constraint
    def _add_login_for_create(self, data):
        partner = self.env["res.partner"].browse(data["partner_id"])
        data["login"] = partner.email

    @api.model_create_multi
    def create(self, data_list):
        for data in data_list:
            self._add_login_for_create(data)
        return super().create(data_list)

    @api.depends("partner_id.email")
    def _compute_login(self):
        for record in self:
            record.login = record.partner_id.email

    def _crypt_context(self):
        return DEFAULT_CRYPT_CONTEXT

    def _check_no_empty(self, login, password):
        # double check by security but calling this through a service should
        # already have check this
        if not (
            isinstance(password, str) and password and isinstance(login, str) and login
        ):
            _logger.warning("Invalid login/password for sign in")
            raise AccessDenied()

    def _get_hashed_password(self, directory, login):
        self.flush()
        self.env.cr.execute(
            """
            SELECT id, COALESCE(encrypted_password, '')
            FROM auth_partner
            WHERE login=%s AND directory_id=%s""",
            (login, directory.id),
        )
        hashed = self.env.cr.fetchone()
        if hashed and hashed[1]:
            # ensure that we have a auth.partner and this partner have a password set
            return hashed
        else:
            raise AccessDenied()

    def _compute_password(self):
        for record in self:
            record.password = ""

    def _inverse_password(self):
        # TODO add check on group
        for record in self:
            ctx = record._crypt_context()
            record.encrypted_password = ctx.encrypt(record.password)
            record.password = ""

    def _prepare_partner_auth_signup(self, directory, vals):
        return {
            "login": vals["login"],
            "password": vals["password"],
            "directory_id": directory.id,
        }

    def _prepare_partner_signup(self, directory, vals):
        return {
            "name": vals["name"],
            "email": vals["login"],
            "auth_partner_ids": [
                (0, 0, self._prepare_partner_auth_signup(directory, vals))
            ],
        }

    @api.model
    def _signup(self, directory, **vals):
        partner = self.env["res.partner"].create(
            [
                self._prepare_partner_signup(directory, vals),
            ]
        )
        auth_partner = partner.auth_partner_ids
        directory._send_mail(
            "invite_validate_email",
            auth_partner,
            token=auth_partner._generate_token_mail_validation(),
        )
        return auth_partner

    @api.model
    def _login(self, directory, **vals):
        login = vals["login"]
        password = vals["password"]

        self._check_no_empty(login, password)
        try:
            _id, hashed = self._get_hashed_password(directory, login)
            valid, replacement = self._crypt_context().verify_and_update(
                password, hashed
            )

            auth_partner = valid and self.browse(_id)
        except AccessDenied:
            # We do not want to leak information about the login,
            # always raise the same exception
            auth_partner = None

        if not auth_partner:
            raise AccessDenied(_("Invalid Login or Password"))

        if replacement is not None:
            auth_partner.encrypted_password = replacement

        return auth_partner

    @api.model
    def _validate_email(self, directory, token_mail_validation):
        hashed_token = self._encrypt_token(token_mail_validation)
        auth_partner = self.search(
            [
                ("token_mail_validation_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if auth_partner:
            auth_partner.write(
                {
                    "token_mail_validation_encrypted": False,
                    "mail_verified": True,
                }
            )
            return auth_partner
        else:
            raise UserError(_("Invalid Token, please request a new one"))

    def _get_impersonate_url(self, token, **kwargs):
        # You should override this method according to the impersonation url
        # your framework is using

        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url = f"{base}/auth/impersonate/{self.id}/{token}"
        return url

    def _get_impersonate_action(self, token, **kwargs):
        return {
            "type": "ir.actions.act_url",
            "url": self._get_impersonate_url(token, **kwargs),
            "target": "self",
        }

    def impersonate(self):
        self.ensure_one()
        if self.env.user not in self.impersonating_user_ids:
            raise AccessDenied(_("You are not allowed to impersonate this user"))

        token = random_token()
        expiration = datetime.now() + timedelta(
            minutes=self.directory_id.impersonating_token_duration
        )
        self.write(
            {
                "token_impersonating_encrypted": self._encrypt_token(token),
                "token_impersonating_expiration": expiration,
            }
        )

        return self._get_impersonate_action(token)

    @api.depends_context("uid")
    def _compute_user_can_impersonate(self):
        for record in self:
            record.user_can_impersonate = self.env.user in record.impersonating_user_ids

    def _impersonating(self, directory, auth_partner_id, token):
        hashed_token = self._encrypt_token(token)
        auth_partner = self.search(
            [
                ("id", "=", auth_partner_id),
                ("token_impersonating_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if (
            auth_partner
            and auth_partner.token_impersonating_expiration > datetime.now()
        ):
            auth_partner.write(
                {
                    "token_impersonating_encrypted": False,
                    "token_impersonating_expiration": False,
                }
            )

            return auth_partner
        else:
            raise UserError(_("Invalid Token, please request a new one"))

    def _on_reset_password_sent(self):
        self.ensure_one()
        self.date_last_request_reset_pwd = fields.Datetime.now()
        self.date_last_sucessfull_reset_pwd = None
        self.nbr_pending_reset_sent += 1

    def _send_invite(self):
        self.ensure_one()
        self.directory_id._send_mail(
            "invite_set_password",
            self,
            callback_job=self.delayable()._on_reset_password_sent(),
            token=self._generate_token(),
        )

    def send_invite(self):
        for rec in self:
            rec.send_invite()

    def _request_reset_password(self):
        return self.directory_id._send_mail(
            "request_reset_password",
            self,
            callback_job=self.delayable()._on_reset_password_sent(),
            token=self._generate_token(),
        )

    def _set_password(self, directory, token_set_password, password):
        hashed_token = self._encrypt_token(token_set_password)
        auth_partner = self.search(
            [
                ("token_set_password_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if auth_partner and auth_partner.token_expiration > datetime.now():
            auth_partner.write(
                {
                    "password": password,
                    "token_set_password_encrypted": False,
                    "token_expiration": False,
                    "mail_verified": True,
                }
            )
            auth_partner.date_last_sucessfull_reset_pwd = fields.Datetime.now()
            auth_partner.nbr_pending_reset_sent = 0
            return auth_partner
        else:
            raise UserError(_("Invalid Token, please request a new one"))

    def _generate_token(self, force_expiration=None):
        expiration = force_expiration or (
            datetime.now()
            + timedelta(minutes=self.directory_id.set_password_token_duration)
        )
        token = random_token()
        self.write(
            {
                "token_set_password_encrypted": self._encrypt_token(token),
                "token_expiration": expiration,
            }
        )
        return token

    def _generate_token_mail_validation(self):
        token = random_token()
        self.write(
            {
                "token_mail_validation_encrypted": self._encrypt_token(token),
            }
        )
        return token

    def _encrypt_token(self, token):
        return DEFAULT_CRYPT_CONTEXT_TOKEN.hash(token)
