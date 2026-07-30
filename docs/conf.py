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
exclude_patterns = [
    'runtime-integration-notes.md',
]

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['beyin.css']
html_js_files = ['beyin-theme.js']
html_theme_options = {
    'style_external_links': True,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 3,
}
