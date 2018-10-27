# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from Products.CMFPlone.utils import _createObjectByType
from bika.lims import api
from bika.lims.idserver import renameAfterCreation
from bika.lims.utils import tmpID
from senaite.reflex import logger

CONTROL_PANELS = [
    {
        "id": "reflextesting_scenarios",
        "type": "ReflexTestingScenariosFolder",
        "title": "Reflex Testing Scenarios",
        "description": "",
        "insert-after": "*"
    }
]

CATALOGS_BY_TYPE = [
    # Tuples of (type, [catalog])
    ("ReflexTestingScenario", ["bika_setup_catalog"]),
]

INDEXES = [
    # Tuples of (catalog, id, indexed attribute, type)
]

COLUMNS = [
    # Tuples of (catalog, column name)
]


def post_install(portal_setup):
    """Runs after the last import step of the *default* profile

    This handler is registered as a *post_handler* in the generic setup profile

    :param portal_setup: SetupTool
    """
    logger.info("SENAITE REFLEX install handler [BEGIN]")

    # https://docs.plone.org/develop/addons/components/genericsetup.html#custom-installer-code-setuphandlers-py
    profile_id = "profile-senaite.reflex:default"
    context = portal_setup._getImportContext(profile_id)
    portal = context.getSite()  # noqa

    # Setup catalogs
    setup_catalogs(portal)

    # Setup new content types
    setup_control_panels(portal)

    # Migrate old reflex rules from senaite.core
    migrate_core_reflex_rules(portal)

    logger.info("SENAITE REFLEX install handler [DONE]")


def setup_catalogs(portal):
    """Setup Plone catalogs
    """
    logger.info("*** Setup Catalogs ***")

    # Setup catalogs by type
    for type_name, catalogs in CATALOGS_BY_TYPE:
        at = api.get_tool("archetype_tool")
        # get the current registered catalogs
        current_catalogs = at.getCatalogsByType(type_name)
        # get the desired catalogs this type should be in
        desired_catalogs = map(api.get_tool, catalogs)
        # check if the catalogs changed for this portal_type
        if set(current_catalogs).difference(desired_catalogs):
            # fetch the brains to reindex
            brains = api.search({"portal_type": type_name})
            # updated the catalogs
            at.setCatalogsByType(type_name, catalogs)
            logger.info("*** Assign '%s' type to Catalogs %s" %
                        (type_name, catalogs))
            for brain in brains:
                obj = api.get_object(brain)
                logger.info("*** Reindexing '%s'" % repr(obj))
                obj.reindexObject()

    # Setup catalog indexes
    to_index = []
    for catalog, name, attribute, meta_type in INDEXES:
        c = api.get_tool(catalog)
        indexes = c.indexes()
        if name in indexes:
            logger.info("*** Index '%s' already in Catalog [SKIP]" % name)
            continue

        logger.info("*** Adding Index '%s' for field '%s' to catalog ..."
                    % (meta_type, name))
        c.addIndex(name, meta_type)
        to_index.append((c, name))
        logger.info("*** Added Index '%s' for field '%s' to catalog [DONE]"
                    % (meta_type, name))

    for catalog, name in to_index:
        logger.info("*** Indexing new index '%s' ..." % name)
        catalog.manage_reindexIndex(name)
        logger.info("*** Indexing new index '%s' [DONE]" % name)

    # Setup catalog metadata columns
    for catalog, name in COLUMNS:
        c = api.get_tool(catalog)
        if name not in c.schema():
            logger.info("*** Adding Column '%s' to catalog '%s' ..."
                        % (name, catalog))
            c.addColumn(name)
            logger.info("*** Added Column '%s' to catalog '%s' [DONE]"
                        % (name, catalog))
        else:
            logger.info("*** Column '%s' already in catalog '%s'  [SKIP]"
                        % (name, catalog))
            continue


def setup_control_panels(portal):
    """Setup Plone control and Senaite management panels
    """
    logger.info("*** Setup Control Panels ***")

    # get the bika_setup object
    bika_setup = api.get_bika_setup()
    cp = api.get_tool("portal_controlpanel")

    def get_action_index(action_id):
        if action_id == "*":
            action = cp.listActions()[-1]
            action_id = action.getId()
        for n, action in enumerate(cp.listActions()):
            if action.getId() == action_id:
                return n
        return -1

    for item in CONTROL_PANELS:
        id = item.get("id")
        type = item.get("type")
        title = item.get("title")
        description = item.get("description")

        panel = bika_setup.get(id, None)
        if panel is None:
            logger.info("Creating Setup Folder '{}' in Setup.".format(id))
            # allow content creation in setup temporary
            portal_types = api.get_tool("portal_types")
            fti = portal_types.getTypeInfo(bika_setup)
            fti.filter_content_types = False
            myfti = portal_types.getTypeInfo(type)
            global_allow = myfti.global_allow
            myfti.global_allow = True
            folder_id = bika_setup.invokeFactory(type, id, title=title)
            panel = bika_setup[folder_id]
            myfti.global_allow = global_allow
            fti.filter_content_types = True
        else:
            # set some meta data
            panel.setTitle(title)
            panel.setDescription(description)

        # Move configlet action to the right index
        action_index = get_action_index(id)
        ref_index = get_action_index(item["insert-after"])
        if (action_index != -1) and (ref_index != -1):
            actions = cp._cloneActions()
            action = actions.pop(action_index)
            actions.insert(ref_index + 1, action)
            cp._actions = tuple(actions)
            cp._p_changed = 1

        # reindex the object to render it properly in the navigation portlet
        panel.reindexObject()


def migrate_core_reflex_rules(portal):
    """Migrates the existing reflex rules from core to the types of this add-on
    """
    logger.info("*** Migrating Reflex Rules ***")
    folder = portal.bika_setup.reflextesting_scenarios
    for reflex_rule in portal.bika_setup.bika_reflexrulefolder.objectValues():
        obj = _createObjectByType("ReflexTestingScenario", folder, tmpID())
        obj.edit(title=reflex_rule.Title(),
                 Method=reflex_rule.getMethod(),
                 ReflexRules=reflex_rule.getReflexRules())
        obj.unmarkCreationFlag()
        renameAfterCreation(obj)

        # Remove the old reflex rule
        reflex_rule.aq_parent.manage_delObjects([reflex_rule.getId()])
