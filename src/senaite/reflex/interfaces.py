# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from bika.lims.interfaces import IBikaLIMS
from zope.interface import Interface


class ILayer(IBikaLIMS):
    """Layer Interface
    """


class IReflexTestingScenario(Interface):
    """Marker interface for a Reflex Testing Scenario
    """


class IReflexTestingScenariosFolder(Interface):
    """Marker interface for Reflex Testing Scenarios folder
    """
