# PhotoShare Documentation

Run the following command from the project root (Sphinx must be installed in the virtual environment):

```bash
venv/bin/python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in your browser.

The reference documentation is generated from docstrings without importing the application.
Edit the docstrings in the Python modules rather than the generated files in
`docs/_generated/` or `docs/reference.rst`.
The architecture overview and API workflows are documented in `docs/guide.rst`.
