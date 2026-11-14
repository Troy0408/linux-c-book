"""Render the DocBook-generated book index without losing index entries.

The caller supplies ``render_index_text(dt)`` to render each dt's full mixed
content, including all links and their target page references.  This module
owns only grouping and layout.  The input tree has unqualified tag names.
"""


def _escape_heading(value):
    substitutions = {
        '\\': r'\textbackslash{}', '{': r'\{', '}': r'\}',
        '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&',
        '_': r'\_', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}',
    }
    return ''.join(substitutions.get(char, char) for char in value)


def render_index(node, render_index_text):
    """Render an inner ``div.index`` as a breakable, two-column index.

    Each dt is passed exactly once to the callback, including dt elements
    without links.  Nested dd/dl lists are rendered in document order.
    The surrounding document must load the multicol package.
    """
    lines = [r'\begin{multicols}{2}', r'\raggedright']

    def render_list(dl, depth):
        for child in dl:
            if child.tag == 'dt':
                lines.append(
                    r'{\leftskip=' + str(depth) + r'em\relax '
                    r'\hangindent=1em\hangafter=1\noindent '
                    + render_index_text(child) + r'\par}')
            elif child.tag == 'dd':
                for nested in child:
                    if nested.tag == 'dl':
                        render_list(nested, depth + 1)

    for group in node:
        if group.tag != 'div' or group.get('class') != 'indexdiv':
            continue
        for child in group:
            if child.tag == 'h3':
                heading = _escape_heading(''.join(child.itertext()))
                lines.append(r'\par\medskip\noindent\textbf{' + heading + r'}\par\nopagebreak')
            elif child.tag == 'dl':
                render_list(child, 0)
    lines.append(r'\end{multicols}')
    return '\n'.join(lines) + '\n'
