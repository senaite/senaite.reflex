# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

import sys

from AccessControl import ClassSecurityInfo
from Products.Archetypes import atapi
from Products.Archetypes.public import BaseContent
from Products.Archetypes.public import DisplayList
from Products.Archetypes.public import ReferenceField
from Products.Archetypes.public import Schema
from Products.Archetypes.public import SelectionWidget
from Products.Archetypes.references import HoldingReference
from Products.CMFCore.utils import getToolByName
from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_LISTING
from bika.lims.content.bikaschema import BikaSchema
from senaite.reflex import senaiteMessageFactory as _
from senaite.reflex.browser.fields import ReflexTestingRulesField
from senaite.reflex.config import PRODUCT_NAME
from senaite.reflex.interfaces import IReflexTestingScenario
from zope.interface import implements

schema = BikaSchema.copy() + Schema((
    # Methods associated to the Reflex rule
    # In the first place the user has to choose from a drop-down list the
    # method which the rules for the analysis service will be bind to. After
    # selecting the method, the system will display another list in order to
    # choose the analysis service to add the rules when using the selected
    # method.
    ReferenceField(
        'Method',
        required=1,
        multiValued=0,
        vocabulary_display_path_bound=sys.maxint,
        vocabulary='getMethodsDisplayList',
        allowed_types=('Method',),
        relationship='ReflexTestingScenarioMethod',
        referenceClass=HoldingReference,
        widget=SelectionWidget(
            label=_("Method"),
            format='select',
            description=_(
                "Select the method which the rules for the analysis "
                "service will be bound to."),
        )
    ),
    ReflexTestingRulesField('ReflexRules',),
))


class ReflexTestingScenario(BaseContent):
    """Defines a Reflex Testing Scenario
    """
    implements(IReflexTestingScenario)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    @security.private
    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    @security.private
    def getMethodsDisplayList(self):
        """Returns a display list with the active methods
        """
        query = dict(portal_type="Method", inactive_state="active")
        items = api.search(query, "bika_setup_catalog")
        items = map(lambda brain: (brain.UID, brain.Title), items)
        items.sort(lambda x, y: cmp(x[1], y[1]))
        return DisplayList(list(items))

    @security.private
    def _areConditionsMet(self, action_set, analysis, forceuid=False):
        """
        This function returns a boolean as True if the conditions in the
        action_set are met, and returns False otherwise.
        :analysis: the analysis full object which we want to obtain the
            rules for.
        :action_set: a set of rules and actions as a dictionary.
            {'actions': [{'act_row_idx': 0,
                'action': 'setresult',
                'an_result_id': 'set-4',
                'analyst': 'analyst1',
                'otherWS': 'current',
                'setresultdiscrete': '3',
                'setresulton': 'new',
                'setresultvalue': '',
                'worksheettemplate': ''}],
            'conditions': [{'analysisservice': 'dup-2',
                'and_or': 'and',
                'cond_row_idx': 0,
                'discreteresult': '2',
                'range0': '',
                'range1': ''},
                {'analysisservice': 'dup-7',
                'and_or': 'no',
                'cond_row_idx': 1,
                'discreteresult': '2',
                'range0': '',
                'range1': ''}],
            'mother_service_uid': 'ddaa2a7538bb4d188798498d6e675abd',
            'rulenumber': '1',
            'trigger': 'submit'}
        :forceuid: a boolean used to get the analysis service's UID from the
        analysis even if the analysis has been reflected and has a local_id.
        :returns: a Boolean.
        """
        conditions = action_set.get('conditions', [])
        eval_str = ''
        # Getting the analysis local id or its uid instead
        alocalid = analysis.getReflexRuleLocalID() if \
            analysis.getIsReflexAnalysis() and not forceuid else analysis.getServiceUID()
        # Getting the local ids (or analysis service uid) from the condition
        # with the same local id (or analysis service uid) as the analysis
        # attribute
        localids = [cond.get('analysisservice') for cond in conditions
                    if cond.get('analysisservice', '') == alocalid]
        # Now the alocalid could be the UID of the analysis service (if
        # this analysis has not been crated by a previous reflex rule) or it
        # could be a local_id if the analysis has been created by a reflex
        # rule.
        # So, if the analysis was reflexed, and no localid has been found
        # inside the action_set matching the analysis localid, lets look for
        # the analysis service UID.
        # forceuid is True when this second query has been done.
        if not localids and not forceuid and analysis.getIsReflexAnalysis():
            return self._areConditionsMet(action_set, analysis, forceuid=True)
        # action_set will not have any action for this analysis
        elif not localids:
            return False
        # Getting the action_set.rulenumber in order to check the
        # analysis.ReflexRuleActionsTriggered
        rulenumber = action_set.get('rulenumber', '')
        # Getting the reflex rules uid in order to fill the
        # analysis.ReflexRuleActionsTriggered attribute later
        rr_uid = self.UID()
        # Building the possible analysis.ReflexRuleActionsTriggered
        rr_actions_triggered = '.'.join([rr_uid, rulenumber])
        # If the follow condition is met, it means that the action_set for this
        # analysis has already been done by any other analysis from the
        # action_set. (e.g analsys.local_id =='dup-2', but this action has been
        # ran by the analysis with local_id=='dup-1', so we do not have to
        # run it again)
        if rr_actions_triggered in\
                analysis.getReflexRuleActionsTriggered().split('|'):
            return False
        # Check that rules are not repited: lets supose that some conditions
        # are met and an analysis with id analysis-1 is reflexed using a
        # duplicate action. Now we have analysis-1 and analysis1-dup. If the
        # same conditions are met while submitting/verifying analysis1-dup, the
        # duplicated shouldn't trigger the reflex action again.
        if forceuid and analysis.IsReflexAnalysis and rr_actions_triggered in\
                analysis.getReflexRuleActionsTriggered().split('|'):
            return False
        # To save the analysis related in the same action_set
        ans_related_to_set = []
        for condition in conditions:
            # analysisservice can be either a service uid (if it is the first
            # condition in the reflex rule) or it could be a local id such
            # as 'dup-2' if the analysis_set belongs to a derivate rule.
            ans_cond = condition.get('analysisservice', '')
            ans_uid_cond = action_set.get('mother_service_uid', '')
            # Be aware that we already know that the local_id for 'analysis'
            # has been found inside the conditions for this action_set
            if ans_cond != alocalid:
                # If the 'analysisservice' item from the condition is not the
                # same as the local_id from the analysis, the system
                # should look for the possible analysis with this localid
                # (e.g dup-2) and get its analysis object in order to compare
                # the results of the 'analysis variable' with the analysis
                # object obtained here
                curranalysis = _fetch_analysis_for_local_id(
                    analysis, ans_cond)
            else:
                # if the local_id of the 'analysis' is the same as the
                # local_id in the condition, we will use it as the current
                # analysis
                curranalysis = analysis
            if not curranalysis:
                continue
            ans_related_to_set.append(curranalysis)
            # the value of the analysis' result as string
            result = curranalysis.getResult()
            if len(analysis.getResultOptions()) > 0:
                # Discrete result as expacted value
                exp_val = condition.get('discreteresult', '')
            else:
                exp_val = (
                    condition.get('range0', ''),
                    condition.get('range1', '')
                    )
            and_or = condition.get('and_or', '')
            service_uid = curranalysis.getServiceUID()

            # Resolve the conditions
            resolution = \
                ans_uid_cond == service_uid and\
                ((api.is_floatable(result) and isinstance(exp_val, str) and
                    exp_val == result) or
                    (api.is_floatable(result) and
                     len(exp_val) == 2 and
                     api.is_floatable(exp_val[0]) and
                     api.is_floatable(exp_val[1]) and
                        float(exp_val[0]) <= float(result) and
                        float(result) <= float(exp_val[1])))
            # Build a string and then use eval()
            if and_or == 'no':
                eval_str += str(resolution)
            else:
                eval_str += str(resolution) + ' ' + and_or + ' '
        if eval_str and eval(eval_str):
            for an in ans_related_to_set:
                an.addReflexRuleActionsTriggered(rr_actions_triggered)
            return True
        else:
            return False

    @security.public
    def getActionReflexRules(self, analysis, wf_action):
        """
        This function returns a list of dictionaries with the rules to be done
        for the analysis service.
        :analysis: the analysis full object which we want to obtain the
            rules for.
        :wf_action: it is the workflow action that the analysis is doing, we
            have to act in consideration of the action_set 'trigger' variable
        :returns: [{'action': 'duplicate', ...}, {,}, ...]
        """
        # Setting up the analyses catalog
        self.analyses_catalog = getToolByName(self, CATALOG_ANALYSIS_LISTING)
        # Getting the action sets, those that contain action rows
        action_sets = self.getReflexRules()
        rules_list = []
        condition = False
        for action_set in action_sets:
            # Validate the trigger
            if action_set.get('trigger', '') == wf_action:
                # Getting the conditions resolution
                condition = self._areConditionsMet(action_set, analysis)
                if condition:
                    actions = action_set.get('actions', [])
                    for act in actions:
                        # Adding the rule number inside each action row because
                        # need to get the rule number from a row action later.
                        # we will need to get the rule number from a row
                        # action later.
                        act['rulenumber'] = action_set.get('rulenumber', '0')
                        act['rulename'] = self.Title()
                        rules_list.append(act)
        return rules_list

atapi.registerType(ReflexTestingScenario, PRODUCT_NAME)
