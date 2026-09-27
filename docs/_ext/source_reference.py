"""Generate Sphinx Python-domain reference pages without importing application code."""
import ast
from pathlib import Path


def render_node(node, prefix=''):
    """Render documented functions/classes without evaluating defaults or annotations."""
    doc = ast.get_docstring(node)
    if not doc:
        return []
    name = prefix + node.name
    if isinstance(node, ast.ClassDef):
        directive = f'.. py:class:: {name}'
    else:
        kind = 'method' if prefix else 'function'
        # Do not expose evaluated defaults (configuration and dependency objects).
        signature = ast.unparse(node.args)
        directive = f'.. py:{kind}:: {name}({signature})'
    result = [directive, ''] + ['   ' + line if line else '' for line in doc.splitlines()] + ['']
    if isinstance(node, ast.ClassDef):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.extend(render_node(child, name + '.'))
    return result


def generate_reference(app):
    """Refresh source-derived pages before Sphinx discovers documents."""
    root = Path(app.confdir).parent
    output = Path(app.srcdir) / '_generated'
    output.mkdir(exist_ok=True)
    files = [root / 'main.py']
    for folder in ('routes', 'repository', 'services', 'database', 'entity', 'schemas'):
        files.extend(sorted((root / 'src' / folder).glob('*.py')))
    entries = []
    for path in files:
        module = '.'.join(path.relative_to(root).with_suffix('').parts)
        tree = ast.parse(path.read_text(encoding='utf-8'))
        lines = [module, '=' * len(module), '', f'.. py:module:: {module}', '', ast.get_docstring(tree) or '', '']
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                lines.extend(render_node(node))
        target = output / (module + '.rst')
        content = '\n'.join(lines) + '\n'
        if not target.exists() or target.read_text() != content:
            target.write_text(content, encoding='utf-8')
        entries.append('   _generated/' + module)
    content = 'Module reference\n================\n\nGenerated from source docstrings without importing the application.\n\n.. toctree::\n   :maxdepth: 1\n\n' + '\n'.join(entries) + '\n'
    target = Path(app.srcdir) / 'reference.rst'
    if not target.exists() or target.read_text() != content:
        target.write_text(content, encoding='utf-8')


def setup(app):
    """Register the source-reference generator with Sphinx."""
    app.connect('builder-inited', generate_reference)
    return {'version': '1.0', 'parallel_read_safe': True, 'parallel_write_safe': True}
