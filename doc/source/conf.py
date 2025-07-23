# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

# add module path to sys.path
sys.path.insert(0, os.path.abspath("/src/"))

# add _manualsummary (folder in file dir) to sys.path
sys.path.insert(0, os.path.abspath("_manualsummary/"))

# -- Project information -----------------------------------------------------

project = "D2R Nowcasting"
copyright = "MIT License - Copyright (c) 2023-2024 Data2Resilience Team"
author = "Data2Resilience Project Team"

# The full version, including alpha/beta/rc tags
release = 'Development v0.8.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# enable number based figure referencing
numfig = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'classic'
html_theme = "sphinx_rtd_theme"
html_logo = "documentation/data/d2r_logo_II.jpg"
html_favicon = "documentation/data/favicon2/favicon.ico"
html_theme_options = {
    "logo_only": True,
    "collapse_navigation": False,
    "navigation_depth": 4,
}
html_css_files = [
    "css/custom.css",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static'] # Not necessary as we will define the style in the sphinxdoc.Dockerfile


# -- Extension configuration -------------------------------------------------

# Auto-generate documentation from docstrings
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html		# Support for NumPy and Google style docstrings (more readable)
extensions = [
	'sphinx.ext.napoleon',
    'sphinx_new_tab_link',
]

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

#Figure placement within LaTeX paper NOT WORKING
'figure_align': 'ht',

# Footnote with copyright
# derived from https://stackoverflow.com/a/54262480
'preamble': r'''
\makeatletter
\fancypagestyle{normal}{
% this is the stuff in sphinx.sty
\fancyhf{}
\fancyfoot[LE,RO]{{\py@HeaderFamily\thepage}}
% we comment this out and
%\fancyfoot[LO]{{\py@HeaderFamily\nouppercase{\rightmark}}}
%\fancyfoot[RE]{{\py@HeaderFamily\nouppercase{\leftmark}}}
% add copyright stuff
\fancyfoot[LO,RE]{{\textcopyright\ 2025, Data2Resilience Project Team}}
% again original stuff
\fancyhead[LE,RO]{{\py@HeaderFamily \@title\sphinxheadercomma\py@release}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}
}
% this is applied to each opening page of a chapter
\fancypagestyle{plain}{
\fancyhf{}
\fancyfoot[LE,RO]{{\py@HeaderFamily\thepage}}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.4pt}
% add copyright stuff for example at left of footer on odd pages,
% which is the case for chapter opening page by default
\fancyfoot[LO,RE]{{\textcopyright\ 2025, Data2Resilience Project Team.}}
}
\makeatother
''',

}
