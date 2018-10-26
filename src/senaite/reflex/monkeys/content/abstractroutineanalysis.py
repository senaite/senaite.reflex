# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from bika.lims import api
from bika.lims.content.reflexrule import doReflexRuleAction
from bika.lims.interfaces.analysis import IRequestAnalysis
from senaite.reflex import logger


def _reflex_rule_process(self, wf_action):
    """This function does all the reflex rule process.
    :param wf_action: is a string containing the workflow action triggered
    """
    if not IRequestAnalysis.providedBy(self):
        # Only routine analyses (assigned to a Request) are supported
        logger.warn("Only IRequestAnalysis are supported in reflex testing")
        return

    # Check out if the analysis has any reflex rule bound to it.
    # First we have get the analysis' method because the Reflex Rule
    # objects are related to a method.
    a_method = self.getMethod()
    if not a_method:
        return

    # After getting the analysis' method we have to get all Reflex Rules
    # related to that method.
    all_rrs = a_method.getBackReferences('ReflexTestingScenarioMethod')
    if not all_rrs:
        return

    # Once we have all the Reflex Rules with the same method as the
    # analysis has, it is time to get the rules that are bound to the
    # same analysis service that is using the analysis.
    for rule in all_rrs:
        if not api.is_active(rule):
            continue
        # Getting the rules to be done from the reflex rule taking
        # in consideration the analysis service, the result and
        # the state change
        action_row = rule.getActionReflexRules(self, wf_action)
        # Once we have the rules, the system has to execute its
        # instructions if the result has the expected result.
        doReflexRuleAction(self, action_row)
