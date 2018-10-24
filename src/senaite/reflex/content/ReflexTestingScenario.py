# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from Products.Archetypes import atapi
from Products.Archetypes.public import BaseContent
from Products.Archetypes.public import Schema
from bika.lims.content.bikaschema import BikaSchema
from senaite.reflex import senaiteMessageFactory as _
from senaite.reflex.config import PRODUCT_NAME
from senaite.reflex.interfaces import IReflexTestingScenario
from zope.interface import implements

schema = BikaSchema.copy() + Schema((
))
schema['description'].widget.visible = True
schema['description'].widget.label = _("Description")
schema['description'].widget.description = _("")


class ReflexTestingScenario(BaseContent):
    """Defines a Reflex Testing Scenario
    """
    implements(IReflexTestingScenario)
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)


atapi.registerType(ReflexTestingScenario, PRODUCT_NAME)
