# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from operator import itemgetter

from openerp import models
from openerp.http import request


class IrHttp(models.Model):

    _inherit = 'ir.http'

    def _authenticate(self, auth_method='user'):
        res = super(IrHttp, self)._authenticate(auth_method=auth_method)
        # if the env on the request has been accessed before the
        # authentication we must reset the env since it's cached and the
        # user into the env is maybe not set
        objdict = vars(request)
        objdict.pop('env', None)
        return res
