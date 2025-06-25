# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class APILogCollection(models.AbstractModel):
    _name = "api.log_collection.mixin"
    _description = "Collection of API logs"

    log_requests = fields.Boolean(
        help="Log requests in database.",
    )

    log_ids = fields.One2many(
        comodel_name="api.log",
        compute="_compute_log_ids",
        string="Logs",
    )

    def _compute_log_ids(self):
        for collection in self:
            collection.log_ids = self.env["api.log"].search(
                [("collection_ref", "=", "%s,%s" % (collection._name, collection.id))]
            )

    def action_logs(self):
        collections_refs = [
            "%s,%s" % (collection._name, collection.id) for collection in self
        ]
        return {
            "type": "ir.actions.act_window",
            "res_model": "api.log",
            "name": "Logs",
            "view_type": "form",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                (
                    "collection_ref",
                    "in",
                    collections_refs,
                ),
            ],
            "context": dict(self.env.context),
        }
