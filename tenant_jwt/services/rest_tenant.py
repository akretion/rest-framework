# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent


class AuthTenantJwt(AbstractComponent):
    _inherit = "auth.tenant.base"
    _name = "auth.tenant.jwt"
    _usage = "auth"
    _backend = None
    _description = """
    """

    def _sign_in(self, login, password, tenant_model_name):
        tenant = tenant_model_name.sign_in(login, password)
        return tenant

    def _sign_out(self, tenant):
        raise NotImplementedError

    def _reset_password(self, tenant, backend):
        setattr(tenant, tenant._password_hash_field, "")

    def _sign_up(self, login, password):
        self._collection.sign_up(login, password)

    @restapi.method(
        [(["/sign_in/"], "POST")],
        input_param=restapi.Datamodel("input.tenant.sign.in"),
        output_param=restapi.Datamodel("output.tenant.sign.in"),
        auth="public")  # TODO
    def sign_in(self, login, password):
        """
        Get partner's information
        """
        partner = self._get(_id)
        PartnerInfo = self.env.datamodels["partner.info"]
        partner_info = PartnerInfo(partial=True)
        partner_info.id = partner.id
        partner_info.name = partner.name
        partner_info.street = partner.street
        partner_info.street2 = partner.street2
        partner_info.zip_code = partner.zip
        partner_info.city = partner.city
        partner_info.phone = partner.phone
        partner_info.country = self.env.datamodels["country.info"](
            id=partner.country_id.id, name=partner.country_id.name
        )
        partner_info.state = self.env.datamodels["state.info"](
            id=partner.state_id.id, name=partner.state_id.name
        )
        partner_info.is_company = partner.is_company
        return partner_info

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=restapi.Datamodel("partner.search.param"),
        output_param=restapi.Datamodel("partner.short.info", is_list=True),
        auth="public",
    )
    def search(self, partner_search_param):
        """
        Search for partners
        :param partner_search_param: An instance of partner.search.param
        :return: List of partner.short.info
        """
        domain = []
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
        res = []
        PartnerShortInfo = self.env.datamodels["partner.short.info"]
        for p in self.env["res.partner"].search(domain):
            res.append(PartnerShortInfo(id=p.id, name=p.name))
        return res

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        return self.env["res.partner"].browse(_id)
