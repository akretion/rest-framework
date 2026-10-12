# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import os
import unittest
from typing import Annotated

from odoo.tests.common import HttpCase

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner
from odoo.addons.fastapi.routers import demo_router

from fastapi import Depends


# Extend the demo router to have an endpoint that changes a partner name
@demo_router.post("/demo/change_partner_name")
async def change_partner_name(
    data: dict,
    partner: Annotated[Partner, Depends(authenticated_partner)],
) -> dict:
    partner.name = data.get("name")
    return {"name": partner.name}


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class FastAPIHttpCase(HttpCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = self.env(
            context=dict(
                self.env.context,
                tracking_disable=False,
            )
        )
        self.fastapi_demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        self.fastapi_demo_app.demo_auth_method = "api_key"
        self.fastapi_demo_app._handle_registry_sync()
        self.endpoint = self.env.ref("fastapi.fastapi_endpoint_demo")

        self.demo_user = self.env.ref("fastapi.my_demo_app_user")
        self.partner = self.demo_user.partner_id

    def test_change_partner_name(self) -> None:
        route = "/fastapi_demo/demo/change_partner_name"
        messages = self.partner.message_ids
        response = self.url_open(
            route,
            timeout=20,
            data='{"name": "New Name"}',
            headers={
                "API-KEY": "my_demo_app_user",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.partner.name, "New Name")

        message = self.partner.message_ids - messages
        self.assertEqual(len(message), 1)
        self.assertEqual(message.author_id, self.partner)
        self.assertEqual(message.subtype_id.name, "demo")
        self.assertEqual(message.subtype_id.description, "Via Fastapi Demo Endpoint")
