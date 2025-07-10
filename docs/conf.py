# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os  
import sys  
sys.path.insert(0, os.path.abspath('../cyclarity_in_vehicle_sdk'))

project = 'cyclarity-in-vehicle-sdk'
copyright = '2025, Cymotive'
author = 'Cymotive'
release = '1.1.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [  
    'sphinx.ext.autodoc',  
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',  
    'sphinx.ext.autosummary', 
    'myst_parser',
    'sphinxcontrib.autodoc_pydantic',
]  

autodoc_pydantic_field_doc_policy = 'description'
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autosummary_generate = True  # Turn on sphinx.ext.autosummary
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

autosummary_generate = True  

# -- Options for LaTeX output ------------------------------------------------  
  
latex_elements = {  
    # Override the printindex directive to remove the index  
    'printindex': '',
}  