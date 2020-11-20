from odoo.addons.datamodel.fields import NestedModel

from odoo.addons.datamodel.core import Datamodel


class Parent(Datamodel):
    _name = "parent"

    children = NestedModel("child", many=True)
