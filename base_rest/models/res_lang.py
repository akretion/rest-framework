# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from operator import itemgetter

from openerp import api, models, tools


class ResLang(models.Model):

    _inherit = 'res.lang'

    @api.model
    @tools.ormcache()
    def get_installed(self):
        """ Return the installed languages as a list of (code, name) sorted by name. """
        langs = self.with_context(active_test=True).search([])
        return sorted([(lang.code, lang.name) for lang in langs],
                      key=itemgetter(1))

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(ResLang, self).create(vals)

    @api.multi
    def write(self, vals):
        self.clear_caches()
        return super(ResLang, self).write(vals)

    @api.multi
    def unlink(self):
        self.clear_caches()
        return super(ResLang, self).unlink()
