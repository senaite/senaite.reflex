# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from datetime import datetime

from bika.lims import api
from bika.lims.content.reflexrule import _fetch_analysis_for_local_id
from bika.lims.interfaces.analysis import IRequestAnalysis
from bika.lims.utils.analysis import duplicateAnalysis
from bika.lims.workflow import doActionFor
from senaite.reflex import logger


def doActionToAnalysis(source_analysis, action):
    """
    This functions executes the action against the analysis.
    :base: a full analysis object. The new analyses will be cloned from it.
    :action: a dictionary representing an action row.
        [{'action': 'duplicate', ...}, {,}, ...]
    :returns: the new analysis
    """
    if not IRequestAnalysis.providedBy(source_analysis):
        # Only routine analyses (assigned to a Request) are supported
        logger.warn("Only IRequestAnalysis are supported in reflex testing")
        return None

    state = api.get_review_status(source_analysis)
    action_id  = action.get('action', '')
    if action_id == 'setvisibility':
        action_rule_name = 'Visibility set'
        target_id = action.get('setvisibilityof', '')
        if target_id == "original":
            analysis = source_analysis
        else:
            analysis = _fetch_analysis_for_local_id(source_analysis, target_id)

    elif action_id == 'repeat' and state != 'retracted':
        # Repeat an analysis consist on cancel it and then create a new
        # analysis with the same analysis service used for the canceled
        # one (always working with the same sample). It'll do a retract
        # action
        doActionFor(source_analysis, 'retract')
        analysis_request = source_analysis.getRequest()
        analysis = analysis_request.getAnalyses(sort_on="created")[-1]
        analysis = api.get_object(analysis)
        action_rule_name = 'Repeated'
        analysis.setResult('')

    elif action_id == 'duplicate' or state == 'retracted':
        analysis = duplicateAnalysis(source_analysis)
        action_rule_name = 'Duplicated'
        analysis.setResult('')

    elif action_id == 'setresult':
        target = action.get('setresulton', '')
        action_rule_name = 'Result set'
        result_value = action.get('setresultdiscrete', '') or \
                       action['setresultvalue']

        if target == 'original':
            analysis = source_analysis.getOriginalReflexedAnalysis()
            analysis.setResult(result_value)

        elif target == 'new':
            # Create a new analysis
            analysis = duplicateAnalysis(source_analysis)
            analysis.setResult(result_value)
            doActionFor(analysis, 'submit')

        else:
            logger.error("Unknown 'setresulton' directive: {}".format(target))
            return None
    else:
        logger.error("Unknown Reflex Rule action: {}".format(action_id))
        return None

    analysis.setReflexRuleAction(action_id)
    analysis.setIsReflexAnalysis(True)
    analysis.setReflexAnalysisOf(source_analysis)
    analysis.setReflexRuleActionsTriggered(
        source_analysis.getReflexRuleActionsTriggered()
    )
    if action.get('showinreport', '') == "invisible":
        analysis.setHidden(True)
    elif action.get('showinreport', '') == "visible":
        analysis.setHidden(False)
    # Setting the original reflected analysis
    if source_analysis.getOriginalReflexedAnalysis():
        analysis.setOriginalReflexedAnalysis(
            source_analysis.getOriginalReflexedAnalysis())
    else:
        analysis.setOriginalReflexedAnalysis(source_analysis)
    analysis.setReflexRuleLocalID(action.get('an_result_id', ''))

    # Setting the remarks to base analysis
    time = datetime.now().strftime('%Y-%m-%d %H:%M')
    rule_num = action.get('rulenumber', 0)
    rule_name = action.get('rulename', '')
    base_remark = "Reflex rule number %s of '%s' applied at %s." % \
        (rule_num, rule_name, time)
    base_remark = source_analysis.getRemarks() + base_remark + '||'
    source_analysis.setRemarks(base_remark)
    # Setting the remarks to new analysis
    analysis_remark = "%s due to reflex rule number %s of '%s' at %s" % \
        (action_rule_name, rule_num, rule_name, time)
    analysis_remark = analysis.getRemarks() + analysis_remark + '||'
    analysis.setRemarks(analysis_remark)
    return analysis
