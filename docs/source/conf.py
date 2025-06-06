# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import os

import django

from pathlib import Path

from pkg_resources import get_distribution

# Ensure that Django has been configured to avoid import errors on
# automodule / autoclass documentation
sys.path.insert(0, os.path.abspath('../../src/bitu'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'bitu.test_settings'
django.setup()

# Adjust path
sys.path.insert(0, Path('.').__str__())

#sys.path.insert(0, Path(__file__).parent.parent.resolve())

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Bitu'
copyright = '2024, Wikimedia Foundation'
author = 'Simon Lyngshede'
release = '0.1.11'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx_autodoc_typehints",
    "sphinxarg.ext",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autosummary_generate = True
autodoc_mock_imports = ["django"]

# Type hints settings
typehints_fully_qualified = True
always_document_param_types = False
typehints_document_rtype = True
typehints_use_rtype = True
typehints_defaults = "comma"
typehints_use_signature = True
typehints_use_signature_return = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
#html_static_path = ['_static']

# Autodoc settings
autodoc_default_options = {
    # Using None as value instead of True to support the version of Sphinx used in Buster
    "members": None,
    "member-order": "groupwise",
    "show-inheritance": None,
}
autoclass_content = "both"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

