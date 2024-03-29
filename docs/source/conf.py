# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath("."))

import dolor

# -- Project information -----------------------------------------------------

project   = "dolor"
copyright = "2021, dolor authors"
author    = "dolor authors"
version   = dolor.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
]

napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

add_module_names     = False
autoclass_content    = "both"
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_rtd_theme

html_theme      = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

def process_docstring(app, what, name, obj, options, lines):
    # If an object's docstring has :meta no-undoc-members:,
    # then disable documenting members with no docstring.

    to_remove = -1

    for i, line in enumerate(lines):
        if line.strip() == ":meta no-undoc-members:":
            options["undoc-members"] = False

            to_remove = i

            break

    if to_remove >= 0:
        lines.pop(to_remove)

def setup(app):
    app.connect("autodoc-process-docstring", process_docstring)
