"""Convert DocBook XHTML tables to page-breaking LaTeX tables.

``render_table(table, render)`` calls ``render(cell)`` once per td/th;
that callback must render the cell's own text and descendants (including their
tails), but not the cell's outer tag or its own tail. Nested table callbacks
must use ``nested=True``. Requires array, longtable, multirow, ragged2e and
varwidth (via L/C/R column types defined in config/commands.tex).
A top-level caption may be supplied as LaTeX in the opening table row.
"""
from __future__ import annotations

import math
import re

# Usable text width on A4 with 22mm left/right margins (in pt).
_LINEWIDTH_PT = 472.3


def _span(cell, name):
    try:
        return max(1, int(cell.get(name, '1')))
    except ValueError:
        return 1


def _rows(table):
    """Only direct rows: never accidentally pull rows out of nested tables."""
    for child in table:
        if child.tag == 'tr':
            yield child
        elif child.tag in ('thead', 'tbody', 'tfoot'):
            yield from (r for r in child if r.tag == 'tr')


def _cell_metrics(cell):
    """Return (max_line_width, total_width) in half-width character units."""
    lines = []

    def push_text(text, buf, in_code):
        parts = text.splitlines()
        for idx, part in enumerate(parts):
            buf.append((part, in_code))
            if idx < len(parts) - 1:
                lines.append(list(buf))
                buf.clear()

    def collect(node, buf, in_code=False):
        tag = node.tag
        if tag in ('p', 'li', 'div') and buf:
            lines.append(list(buf))
            buf.clear()
        if tag == 'li':
            buf.append(('1.  ', False))
        child_code = in_code or tag == 'code'
        if node.text:
            text = node.text.lstrip() if (tag == 'p' and not buf) else node.text
            push_text(text, buf, child_code)
        for child in node:
            if child.tag == 'br':
                lines.append(list(buf))
                buf.clear()
            else:
                collect(child, buf, child_code)
            if child.tail:
                push_text(child.tail, buf, in_code)
        if tag in ('p', 'li', 'div') and buf:
            lines.append(list(buf))
            buf.clear()

    buf = []
    collect(cell, buf)
    if buf:
        lines.append(buf)

    max_w = 1.0
    total_w = 0.0
    for segments in lines:
        line_w = 0.0
        has_content = False
        for seg_text, seg_code in segments:
            cleaned = re.sub(r'[ \t\r\n]+', ' ', seg_text.replace('\u00a0', ' '))
            if not cleaned.strip() and not has_content:
                cleaned = cleaned.lstrip()
            if cleaned.strip():
                has_content = True
            ascii_w = 1.15 if seg_code else 1.05
            line_w += sum(2.0 if ord(c) >= 0x2e80 else ascii_w for c in cleaned)
        if has_content:
            max_w = max(max_w, line_w)
            total_w += line_w
    return max_w, max(1.0, total_w)


def _layout(table):
    rows, occupied, max_widths, prose_weights = [], {}, [], []
    has_span = False
    headers = {row for group in table.findall('thead') for row in group.findall('tr')}
    for row in _rows(table):
        entries, col = [], 0
        for cell in row:
            if cell.tag not in ('td', 'th'):
                continue
            while occupied.get(col, 0):
                col += 1
            cs, rs = _span(cell, 'colspan'), _span(cell, 'rowspan')
            if cs > 1 or rs > 1:
                has_span = True
            entries.append((col, cs, rs, cell))
            if rs > 1:
                for i in range(col, col + cs):
                    occupied[i] = rs
            mw, tw = _cell_metrics(cell)
            while len(max_widths) < col + cs:
                max_widths.append(1.0)
                prose_weights.append(1.0)
            if cs == 1:
                max_widths[col] = max(max_widths[col], mw)
                prose_weights[col] = max(prose_weights[col], math.sqrt(min(250.0, tw)))
            else:
                for i in range(col, col + cs):
                    max_widths[i] = max(max_widths[i], mw / cs)
                    prose_weights[i] = max(prose_weights[i], math.sqrt(min(250.0, tw) / cs))
            col += cs
        rows.append((entries, set(occupied), row in headers))
        occupied = {i: remaining - 1 for i, remaining in occupied.items() if remaining > 1}
    return rows, max_widths, prose_weights, has_span


def _compute_fractions(summary, max_widths, prose_weights, has_span):
    ncols = len(max_widths)
    if summary == 'Memory Hierarchy':
        return [.135, .115, .165, .200, .125, .260], 3.0, True
    if summary == '如何做类型转换':
        return [.285, .305, .255, .155], 3.0, True
    if has_span:
        total = sum(prose_weights)
        return [.45 / ncols + .55 * w / total for w in prose_weights], 3.0, True

    tabsep = 4.0 if ncols >= 5 else 6.0
    nat_pt = [max(22.0, w * 5.4 + 6.0) + 2 * tabsep for w in max_widths]
    total_nat = sum(nat_pt)
    if total_nat <= _LINEWIDTH_PT:
        extra = _LINEWIDTH_PT - total_nat
        fractions = [
            (nat_pt[i] + extra * (nat_pt[i] / total_nat)) / _LINEWIDTH_PT
            for i in range(ncols)
        ]
        return fractions, tabsep, False

    # Lock genuinely narrow columns at natural width; share the remainder.
    cap_pt = [0.0] * ncols
    rem_pt = _LINEWIDTH_PT
    rem_cols = set(range(ncols))
    for i in sorted(range(ncols), key=lambda idx: nat_pt[idx]):
        if nat_pt[i] <= 0.85 * (rem_pt / len(rem_cols)):
            cap_pt[i] = nat_pt[i]
            rem_pt -= nat_pt[i]
            rem_cols.remove(i)
        else:
            break
    if rem_cols:
        rem_w = sum(prose_weights[i] for i in rem_cols)
        for i in rem_cols:
            cap_pt[i] = rem_pt * (prose_weights[i] / rem_w)
    return [c / _LINEWIDTH_PT for c in cap_pt], tabsep, False


def render_table(node, render, *, nested=False, caption=None):
    """Render an XHTML table. ``render`` must render a cell's contents.

    Compact tables shrink to their natural content width via varwidth ``L``/``C``/``R``
    columns and center on the page; wide tables cap column budgets within
    ``\\linewidth`` so long prose wraps cleanly without overflow.
    """
    rows, max_widths, prose_weights, has_span = _layout(node)
    if not rows or not max_widths:
        return ''
    ncols = len(max_widths)
    summary = node.get('summary', '')
    fractions, tabsep, fixed_p = _compute_fractions(summary, max_widths, prose_weights, has_span)

    def width(start, count):
        f = sum(fractions[start:start + count])
        return r'\dimexpr %.6f\linewidth-2\tabcolsep\relax' % f

    def spec(start, count=1, align='left'):
        if fixed_p:
            directive = {'center': r'\Centering', 'right': r'\RaggedLeft'}.get(align, r'\RaggedRight')
            return r'>{%s\arraybackslash}p{%s}' % (directive, width(start, count))
        col_type = {'center': 'C', 'right': 'R'}.get(align, 'L')
        return r'%s{%s}' % (col_type, width(start, count))

    columns = ''.join(spec(i) for i in range(ncols))
    env = 'tabular' if nested else 'longtable'
    out = [r'\begingroup', r'\setlength{\tabcolsep}{%gpt}' % tabsep, r'\small', r'\sloppy',
           r'\renewcommand{\arraystretch}{1.16}', r'\setlength{\parskip}{0pt}',
           r'\begin{%s}{%s}' % (env, columns)]
    if caption:
        out.append(caption)
    out.append(r'\toprule')
    header = []
    body = []
    body_rows = [(idx, entries, occupied) for idx, (entries, occupied, is_header) in enumerate(rows) if not is_header]
    last_body_idx = body_rows[-1][0] if body_rows else -1

    for idx, (entries, occupied, is_header) in enumerate(rows):
        by_col = {entry[0]: entry for entry in entries}
        parts, col = [], 0
        while col < ncols:
            if col not in by_col:
                parts.append('')
                col += 1
                continue
            _, cs, rs, cell = by_col[col]
            value = render(cell).strip()
            if summary == '一个语句的三种表示' and col == 1 and not is_header:
                if value == r'a=\BookSplit{}b+\BookSplit{}1;':
                    value = r'\BookCode{' + value + '}'
                elif value.startswith(r'\begin{BookLiteral}'):
                    value = value.replace(r'\begin{BookLiteral}', r'\begin{BookLiteral}\ttfamily', 1)
            if cell.tag == 'th':
                value = r'{\bfseries ' + value + '}'
            if rs > 1:
                value = r'\multirow{%d}{=}{%s}' % (rs, value)
            alignment = cell.get('align', '').lower()
            if cs > 1 or alignment in ('left', 'center', 'right'):
                value = r'\multicolumn{%d}{%s}{%s}' % (cs, spec(col, cs, alignment), value)
            parts.append(value)
            col += cs
        result = header if is_header else body
        result.append(' & '.join(parts) + r' \\')
        if not occupied and not is_header and idx != last_body_idx:
            space = '4pt' if summary == '一个语句的三种表示' else '2pt'
            result.append(r'\addlinespace[%s]' % space)
    out.extend(header)
    if header:
        out.append(r'\midrule')
        if not nested:
            out.extend([r'\endfirsthead', r'\toprule', *header, r'\midrule', r'\endhead'])
    out.extend(body)
    out.append(r'\bottomrule')
    out += [r'\end{%s}' % env, r'\endgroup']
    return '\n'.join(out) + '\n'
