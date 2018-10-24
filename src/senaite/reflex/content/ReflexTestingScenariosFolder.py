# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from Products.ATContentTypes.content import schemata
from Products.Archetypes import atapi
from plone.app.folder.folder import ATFolder
from plone.app.folder.folder import ATFolderSchema
from senaite.reflex.config import PRODUCT_NAME
from senaite.reflex.interfaces import IReflexTestingScenariosFolder
from zope.interface.declarations import implements

schema = ATFolderSchema.copy()

class ReflexTestingScenariosFolder(ATFolder):
    """Defines a Reflex Testing Scenarios Folder
    """
    implements(IReflexTestingScenariosFolder)
    displayContentsTab = False
    schema = schema


schemata.finalizeATCTSchema(schema, folderish=True, moveDiscussion=False)
atapi.registerType(ReflexTestingScenariosFolder, PRODUCT_NAME)
