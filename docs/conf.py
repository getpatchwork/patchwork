# -*- coding: utf-8 -*-
#
# Patchwork documentation build configuration file

import os
import sys

PATCHWORK_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PATCHWORK_DIR)

from patchwork import VERSION  # noqa


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '1.5'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.todo',
    'reno.sphinxext',
    'sphinxcontrib.openapi'
]

# The theme to use for HTML and HTML Help pages.
html_theme = 'sphinx_rtd_theme'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Patchwork'
copyright = u'2018-2019, Patchwork Developers'
author = u'Patchwork Developers'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '.'.join((str(x) for x in VERSION[:3]))
# The full version, including alpha/beta/rc tags.
release = '.'.join((str(x) for x in VERSION))

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False
