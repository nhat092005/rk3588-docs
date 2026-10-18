project = "RK3588 PPE Docs"
author = "nhat092005"
language = "vi"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.mermaid",
]
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 1
bibtex_bibfiles = ["refs.bib"]

exclude_patterns = ["_build", ".venv", "README.rst", "tools"]
templates_path = ["_templates"]
html_title = "RK3588 PPE Docs"

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "sticky_navigation": True,
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["zoom.js"]
html_show_copyright = False
html_show_sphinx = False
