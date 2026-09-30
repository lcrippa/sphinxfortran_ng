# Configuration file for the Sphinx documentation builder.

from __future__ import annotations

import os
import sys
from datetime import datetime


# -- Path setup --------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))

# The package lives in ``../src``: make it importable when building the docs
# from a repository checkout (needed by ``sphinx.ext.autodoc`` in api.rst).
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "src")))


# -- Project information -----------------------------------------------------

project = "sphinxfortran_ng"
author = "SciFortran contributors"
copyright = f"{datetime.now().year}, {author}"

# The full version, including alpha/beta/rc tags
try:
    import sphinxfortran_ng
    release = sphinxfortran_ng.__version__
except Exception:
    release = "unknown"


# -- General configuration ---------------------------------------------------

extensions = [
    # Core Sphinx extensions
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",

    # Fortran support. Both are needed: the domain registers the ``f:``
    # directives and roles, the autodoc extension adds the ``f:auto*``
    # directives to that domain.
    "sphinxfortran_ng.fortran_domain",
    "sphinxfortran_ng.fortran_autodoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"

source_suffix = ".rst"
master_doc = "index"


# -- Autodoc configuration (Python API, see api.rst) -------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autodoc_member_order = "bysource"


# -- Fortran autodoc configuration ------------------------------------------

# Files, globs or directories containing the Fortran sources.
# Directories are NOT searched recursively.
# Here: the two example modules that are documented live in examples.rst
# (``examples/SF_ARRAYS.f90`` and ``examples/ED_INPUT_VARS.f90``).
fortran_src = [
    os.path.join(HERE, "examples"),
]

# Extensions looked for in the directories of ``fortran_src`` (case-insensitive)
fortran_ext = [
    "f",
    "f90",
    "f95",
    "f03",
]

# Indentation of the generated reST: an integer (number of spaces),
# "tab" or "space". Default: 4
fortran_indent = 4

# Underline character of the titles generated when a module is documented
# with ``:subsection_type: title``. Default: "-"
fortran_title_underline = "-"


# -- HTML output ------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_title = project

html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "titles_only": False,
}


# -- Intersphinx ------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}


# -- Index / cross-reference behavior ---------------------------------------

# Show Fortran objects in the general index
add_module_names = False


# -- Warnings / nitpicky mode ------------------------------------------------

# Set to True to get a warning for every unresolved cross-reference. It is
# off here because the example modules use routines and modules of SciFortran
# (parse_input_variable, sf_iotools, ...) that are not documented in this
# project, and the Python API page refers to many standard-library types.
nitpicky = False

# Example of how to silence a known false positive when nitpicky is on
nitpick_ignore = [
    ("f:module", "iso_c_binding"),
]


# -- Misc -------------------------------------------------------------------

# Make sure ReST blocks are interpreted strictly
rst_prolog = """
.. role:: f(code)
   :language: fortran
"""
