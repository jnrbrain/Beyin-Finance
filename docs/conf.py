import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Beyin Finance API'
author = 'Said Uludağ'
release = '2.0.0'
copyright = '2026, Beyin Finance'

extensions = [
    'myst_parser',
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
