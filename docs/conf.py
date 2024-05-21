# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import re
import sys


# Function to extract the version from __version__.py
def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(
            os.path.join(here, '../../__version__.py'),
            encoding='utf-8') as f:
        version_file_contents = f.read()
    # Use regular expression to extract version string
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file_contents,
        re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = 'PyEconomics'
author = 'Nathan Ramos, CFA'

# The full version, including alpha/beta/rc tags
version = get_version()
release = get_version()

# Avoid shadowing the built-in 'copyright' name
project_copyright = '2024, Nathan Ramos, CFA'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Exclude members from being documented
autodoc_default_options = {
    'exclude-members': 'API_BASE_URL, PRO_API_BASE_URL'
}

# Configure the source suffix to include both 'data.rst' and '.md' file types
source_suffix = ['.rst', '.md']
source_encoding = 'utf-8'
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for EPUB output -------------------------------------------------

# EPUB settings
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = '2024, Nathan Ramos, CFA'
