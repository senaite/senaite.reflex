# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors.

from senaite.reflex import logger


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

    logger.info("SENAITE REFLEX install handler [DONE]")
