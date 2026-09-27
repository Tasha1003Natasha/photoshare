"""Sphinx configuration; no application imports or environment changes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / '_ext'))
project = 'PhotoShare'
extensions = ['source_reference']
root_doc = 'index'
html_theme = 'alabaster'
exclude_patterns = ['_build', 'README.md']
highlight_language = 'python'
html_title = 'PhotoShare — Developer documentation'
