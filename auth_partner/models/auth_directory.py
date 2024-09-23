# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.delay import chain


class AuthDirectory(models.Model):
    _name = "auth.directory"
    _description = "Auth Directory"

    name = fields.Char(required=True)
    auth_partner_ids = fields.One2many("auth.partner", "directory_id", "Auth Partners")
    set_password_token_duration = fields.Integer(
        default=1440, help="In minute, default 1440 minutes => 24h", required=True
    )
    impersonating_token_duration = fields.Integer(
        default=1, help="In minute, default 1 minute", required=True
    )
    request_reset_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template Forget Password",
        required=True,
        default=lambda self: self.env.ref(
            "auth_partner.email_request_reset_password",
            raise_if_not_found=False,
        ),
    )
    invite_set_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template New Password",
        required=True,
        default=lambda self: self.env.ref(
            "auth_partner.email_invite_set_password",
            raise_if_not_found=False,
        ),
    )
    invite_validate_email_template_id = fields.Many2one(
        "mail.template",
        "Mail Template Validate Email",
        required=True,
        default=lambda self: self.env.ref(
            "auth_partner.email_invite_validate_email",
            raise_if_not_found=False,
        ),
    )
    count_partner = fields.Integer(compute="_compute_count_partner")

    impersonating_user_ids = fields.Many2many(
        "res.users",
        "auth_directory_impersonating_user_rel",
        "directory_id",
        "user_id",
        string="Impersonating Users",
        help="These odoo users can impersonate any partner of this directory",
        default=lambda self: (
            self.env.ref("base.user_root") | self.env.ref("base.user_admin")
        ).ids,
        groups="auth_partner.group_auth_partner_manager",
    )

    def _compute_count_partner(self):
        data = self.env["auth.partner"].read_group(
            [
                ("directory_id", "in", self.ids),
            ],
            ["directory_id"],
            groupby=["directory_id"],
            lazy=False,
        )
        res = {item["directory_id"][0]: item["__count"] for item in data}

        for record in self:
            record.count_partner = res.get(record.id, 0)

    def _get_auth_from_login(self, login):
        # There can be only one auth_partner per login per directory
        return self.auth_partner_ids.filtered(lambda r: r.login == login)

    def _get_template(self, type_or_template):
        if isinstance(type_or_template, str):
            return getattr(self, type_or_template + "_template_id", None)
        return type_or_template

    def _send_mail(
        self, type_or_template, auth_partner, delay=True, callback_job=None, **context
    ):
        """Send an email to the auth_partner using the template defined in the directory"""
        self.ensure_one()
        auth_partner.ensure_one()

        if delay:
            job = self.delayable()._send_mail(
                type_or_template, auth_partner, False, **context
            )
            if callback_job:
                job = chain(job, callback_job)
            return job.delay()

        template = self._get_template(type_or_template)
        if not template:
            raise UserError(
                _("No email template defined for %s in %s", type_or_template, self.name)
            )

        template.sudo().with_context(**(context or {})).send_mail(
            auth_partner.id, force_send=True
        )

        return f"Mail {template} sent to {auth_partner.login}"
