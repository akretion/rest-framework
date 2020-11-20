from odoo.addons.datamodel.tests.common import SavepointDatamodelCase


class TestCrash(SavepointDatamodelCase):
    def test_crash(self):
        to_load = []
        for x in range(100000):
            to_load.append({"name": str(x), "id": x})
        self.env.datamodels["parent"].load({"children": to_load})
