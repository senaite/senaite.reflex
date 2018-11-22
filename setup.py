# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFLEX
#
# Copyright 2018 by it's authors

from setuptools import setup, find_packages

version = "1.0.0"

setup(
    name="senaite.reflex",
    version=version,
    description="Reflex Testing machinery for SENAITE",
    long_description=open("README.rst").read(),
    # long_description_content_type="text/markdown",
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords=['senaite', 'lims', 'opensource'],
    author="SENAITE Foundation",
    author_email="support@senaite.com",
    url="https://github.com/senaite/senaite.reflex",
    license="GPLv2",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    namespace_packages=["senaite"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "senaite.core>=1.2.9",
        "senaite.core<1.3"
        "archetypes.schemaextender",
    ],
    extras_require={
        "test": [
            "Products.PloneTestCase",
            "Products.SecureMailHost",
            "plone.app.testing",
            "unittest2",
        ]
    },
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
