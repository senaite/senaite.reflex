# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from datetime import datetime

from bika.lims import api
from bika.lims.catalog.analysis_catalog import CATALOG_ANALYSIS_LISTING
from bika.lims.interfaces import IAnalysisService
from bika.lims.interfaces.analysis import IRequestAnalysis
from bika.lims.utils import changeWorkflowState
from bika.lims.utils.analysis import duplicateAnalysis, create_analysis
from bika.lims.workflow import doActionFor
from senaite.reflex import logger
from senaite.reflex import senaiteMessageFactory as _


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

    if action_id == "new_analysis":
        # Create a new analysis (different from the original)
        service_uid = action.get("new_analysis", "")
        if not api.is_uid(service_uid):
            logger.error("Not a valid UID: {}".format(service_uid))
            return None
        service = api.get_object_by_uid(service_uid, None)
        if not service or not IAnalysisService.providedBy(service):
            logger.error("No valid service for UID {}".format(service_uid))
            return None

        analysis = create_analysis(source_analysis.aq_parent, service)
        analysis.setSamplePartition(source_analysis.getSamplePartition())
        changeWorkflowState(analysis, "bika_analysis_workflow",
                            "sample_received")
    elif action_id == 'setvisibility':
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
        analysis.setResult('')

    elif action_id == 'duplicate' or state == 'retracted':
        analysis = duplicateAnalysis(source_analysis)
        analysis.setResult('')

    elif action_id == 'setresult':
        target = action.get('setresulton', '')
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
    #remarks = get_remarks(action, analysis)
    #analysis.setRemarks(remarks)

    return analysis


def get_remarks(action, output_analysis):
    action_name = action.get('action', '')
    if not action_name:
        return
    visibility = action.get('showinreport', '')
    visibility = visibility and _(visibility) or ''
    set_visibility = _("Change visibility of {} to {}").format(
        output_analysis.Title(), visibility)
    set_result = _("Set result of {} to {}").format(
        output_analysis.Title(), output_analysis.getFormattedResult())

    destination_map = {
        "current": _("{action_name} {analysis_name} in current worksheet"),
        "to_another": _("{action_name} {analysis_name} in last open worksheet"),
        "create_another":  _("{action_name} {analysis_name} in a new worksheet"),
        "no_ws": _("{action_name} {analysis_name}"),
    }
    analysis_name = output_analysis.Title()
    destination = action.get('otherWS', '')
    actions = {
        'repeat': destination_map.get(destination, '')
            .format(action_name=_("Repeat"), analysis_name=analysis_name),
        'duplicate': destination_map.get(destination, '')
            .format(action_name=_("Duplicate"), analysis_name=analysis_name),
        'new_analysis': destination_map.get(destination, '')
            .format(action_name=_("Add new"), analysis_name=analysis_name),
        'setvisibility': set_visibility.strip(),
        'setresult': set_result.strip(),
    }

    rule_name = "{} '{}'".format(_("Reflex Test"), action.get('rulename', ''))
    remarks = "[{timestamp}] {rule_name} #{rule_number}: {action}".format(
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        rule_name = rule_name,
        rule_number = action.get('rulenumber', '0'),
        action = actions.get(action_name, ''))

    remarks_output = [output_analysis.getRemarks(), remarks]
    remarks_output = filter(lambda rem: rem, remarks_output)
    return '; '.join(remarks_output)


def _fetch_analysis_for_local_id(analysis, ans_cond):
    """
    This function returns an analysis when the derivative IDs conditions
    are met.
    :analysis: the analysis full object which we want to obtain the
        rules for.
    :ans_cond: the local id with the target derivative reflex rule id.
    """
    # Getting the first reflexed analysis from the chain
    first_reflexed = analysis.getOriginalReflexedAnalysis()
    if first_reflexed:
        if api.is_uid(ans_cond) and ans_cond == first_reflexed.getServiceUID():
            return first_reflexed

        # Getting all reflexed analysis created due to this first analysis
        query = dict(getOriginalReflexedAnalysisUID=first_reflexed.UID())
        # From all the related reflexed analysis, return the one that matches
        # with the local id 'ans_cond'
        for derivative in api.search(query, CATALOG_ANALYSIS_LISTING):
            derivative = api.get_object(derivative)
            if derivative.getReflexRuleLocalID() == ans_cond:
                return derivative

    return None
