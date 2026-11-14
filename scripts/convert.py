#!/usr/bin/env python3
"""Convert the mirrored DocBook XHTML to editable chapter, code and map files.

Run from any directory. The inputs are manifest/source.json and its local
files. Typesetting, edition credits and the build are owned by main.tex.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

from pygments import format as format_tokens
from pygments.formatters import LatexFormatter
from pygments.lexers import BashLexer, CLexer, GasLexer, MakefileLexer
from pygments.styles.friendly import FriendlyStyle
from pygments.token import Comment, Error, Number, Whitespace

from book_code import language
from book_index import render_index
from book_math import display_math
from book_tables import render_table


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / 'manifest/source.json'
BASE = 'https://akaedu.github.io/book/'
HEADING = re.compile(r'h[1-4]$')
NUMBER = {
    'part': r'^部分\s+[IVX]+\.\s*',
    'chapter': r'^第\s*\d+\s*章\s*',
    'appendix': r'^附录\s*[A-Z]\.\s*',
    'sect1': r'^\d+\.\s*',
    'sect2': r'^\d+\.\d+\.\s*',
}
CAPTION = re.compile(r'^[图表例]\s+([\dA-Z.]+?)\.\s+')
ADDRESS = re.compile(r"https?://[A-Za-z0-9./_-]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", re.ASCII)
BREAKABLE = re.compile(r'[A-Za-z0-9]+(?:[._~/:=+*×][A-Za-z0-9]*)+')
REFERENCE = re.compile(r'^(?:第\s*([\d.]+)\s*([章节])|附录\s*([A-Z])[.,]?|([图表例])\s*([\dA-Z.]+))\s*')
ESCAPE = {
    '\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '#': r'\#',
    '$': r'\$', '%': r'\%', '&': r'\&', '_': r'\_', '^': r'\textasciicircum{}',
    '~': r'\textasciitilde{}', '<': r'\textless{}', '>': r'\textgreater{}',
    '"': r'\BookQuoteChar{}',
    '\u200b': r'\BookSplit{}', '\u00ad': r'\-',
}
SYMBOLS = '␣↑↓←→↔↕↵↖↗↘↙⌊⌋⌈⌉√≠≤≥∞∧∨⊕⊗∑∈⊂§▁▂▃▄▅▆▇█■□─│┌┐└┘├┤┬┴┼'
ESCAPE.update({c: r'\BookSymbol{' + c + '}' for c in SYMBOLS})
LEXERS = {'C': CLexer, 'Assembler': GasLexer, 'Make': MakefileLexer, 'Shell': BashLexer}


class BookCodeStyle(FriendlyStyle):
    styles = {**FriendlyStyle.styles, Comment: 'italic #3E6268',
              Comment.Special: 'italic #3E6268', Number: '#215F4A',
              Error: '#252D35', Whitespace: ''}


def read(path):
    document = ET.parse(path)
    for node in document.iter():
        node.tag = node.tag.rsplit('}', 1)[-1]
    return document


def cls(node):
    return node.get('class', '')


def txt(node):
    return ''.join(node.itertext())


def normalize(text):
    return ' '.join(text.split())


def escape(text):
    return ''.join(ESCAPE.get(c, c) for c in text)


def prose(text):
    return escape(re.sub(r'\s+', ' ', text or ''))


def technical_prose(text):
    text = re.sub(r'\s+', ' ', text or '')
    def breakable(match):
        return ''.join(escape(char) + (r'\BookSplit{}' if char in '._~/:=+*×' else '')
                       for char in match[0])
    out = []
    start = 0
    for match in BREAKABLE.finditer(text):
        out.extend((escape(text[start:match.start()]), breakable(match)))
        start = match.end()
    out.append(escape(text[start:]))
    return ''.join(out)


def code_text(text, breaks=True):
    # Break after punctuation, and within exceptionally long identifiers.
    pieces = re.split(r'([/_.,;:=|+~@()\[\]-])', text)
    for i in range(0, len(pieces), 2):
        part = pieces[i]
        pieces[i] = r'\BookSplit{}'.join(escape(part[j:j+14]) for j in range(0, len(part), 14)) if breaks else escape(part)
    for i in range(1, len(pieces), 2):
        pieces[i] = escape(pieces[i]) + (r'\BookSplit{}' if breaks else '')
    return ''.join(pieces)


def write(path, data):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = data.encode('utf-8')
    if not dest.exists() or dest.read_bytes() != blob:
        dest.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def only_direct(node, classname):
    return next((child for child in node if cls(child) == classname), None)


def title_of(node):
    titlepage = only_direct(node, 'titlepage')
    return next(h for h in titlepage.iter() if HEADING.fullmatch(h.tag) and cls(h) == 'title')


def source_lines(node, scripts=False):
    """Split an HTML literal layout at br, preserving its inline elements."""
    lines = [[node.text or '']]
    for child in node:
        if child.tag == 'br':
            lines.append([])
        elif scripts and child.tag in ('sub', 'sup'):
            command = '_' if child.tag == 'sub' else '^'
            lines[-1].append(command + '{' + txt(child) + '}')
        else:
            lines[-1].append(child if not scripts else txt(child))
        lines[-1].append((child.tail or '').removeprefix('\n') if child.tag == 'br' else child.tail or '')
    return lines


@dataclass(frozen=True)
class Page:
    record: dict
    root: ET.Element

    @property
    def path(self):
        return self.record['path']

    @property
    def label(self):
        return self.path.removesuffix('.html')

    @property
    def kind(self):
        return self.record['kind']


def load_pages(manifest):
    pages = {}
    for item in manifest['pages']:
        root = next(node for node in read(ROOT / item['file']).getroot().find('body')
                    if cls(node) not in ('navheader', 'navfooter'))
        pages[item['path']] = Page(item, root)
    return pages


def name(page, fragment=''):
    return 'db.' + page.label + ('.' + fragment if fragment else '')


def heading_key(title):
    return re.sub(r'[\s“”"‘’]', '', title)


def reference_key(title, role):
    caption = CAPTION.match(title)
    if caption:
        return title[0], caption[1], heading_key(title[caption.end():])
    prefix = REFERENCE.match(title)
    if prefix:
        number, unit, appendix, category, label = prefix.groups()
        return unit or category or '附录', number or appendix or label, heading_key(title[prefix.end():])
    if role in ('sect1', 'sect2'):
        match = re.match(r'^([\d.]+)\.\s*', title)
        if match:
            return '节', match[1], heading_key(title[match.end():])
    return '', '', heading_key(title)


class Book:
    def __init__(self, manifest, pages):
        self.manifest = manifest
        self.pages = pages
        self.ids = {}
        self.candidates = {}
        self.links = Counter()
        self.missing_links = Counter()
        self.assets = Counter()
        self.blocks = []
        self.counts = Counter()
        self.mapping = []
        self.syntax = LatexFormatter(commandprefix='BK', nowrap=True, style=BookCodeStyle, nobackground=True)
        self.emitted_anchors = set()
        for path, page in pages.items():
            self.ids[path] = {node.get('id') for node in page.root.iter() if node.get('id')}
            candidates = self.candidates[path] = defaultdict(set)
            parents = {child: node for node in page.root.iter() for child in node}
            top_title = title_of(page.root)
            for node in page.root.iter():
                if (HEADING.fullmatch(node.tag) or node.tag == 'p') and cls(node) == 'title':
                    anchor = next((a.get('id') for a in node.iter('a') if a.get('id')), '')
                    if not anchor and node.tag == 'p':
                        anchor = next((a.get('id') for a in parents[node] if a.get('id')), '')
                    title = normalize(txt(node))
                    role = page.kind if node is top_title else 'sect2' if node.tag == 'h3' else ''
                    if title:
                        key = reference_key(title, role)
                        candidates[key].add(anchor)
                        candidates[('', '', key[-1])].add(anchor)

    def target(self, current, href, visible=''):
        url = urlsplit(urljoin(BASE + current.path, href))
        if url.netloc != 'akaedu.github.io' or not url.path.startswith('/book/'):
            return None
        path = unquote(url.path.removeprefix('/book/')) or 'index.html'
        page = self.pages.get(path)
        if page is None:
            return None
        frag = unquote(url.fragment)
        if not frag or frag in self.ids[path]:
            return name(page, frag)
        key = reference_key(normalize(visible), '')
        if key[0] == '附录':
            candidates = {item for keys, values in self.candidates[path].items()
                          if keys[:2] == key[:2] for item in values if item}
        else:
            candidates = self.candidates[path].get(key, set()) - {''}
        if len(candidates) == 1:
            dest = next(iter(candidates))
            self.missing_links[current.path, href, 'title', dest] += 1
            return name(page, dest)
        self.missing_links[current.path, href, 'page', ''] += 1
        return name(page)

    def anchor(self, label):
        if label in self.emitted_anchors:
            return ''
        self.emitted_anchors.add(label)
        return r'\BookAnchor{' + label + '}'

    def record_page(self, page, output):
        self.mapping.append({
            'url': page.record['url'], 'html': page.record['file'],
            'kind': page.kind, 'title': page.record['title'], 'tex': output,
            'label': name(page),
        })

    def source_block(self, page, node, number):
        raw = txt(node)
        hint = language(raw, cls(node), page.path)
        ext = {'Make': 'mk', 'Assembler': 's', 'Shell': 'sh', 'C': 'c'}.get(hint, 'txt')
        stem = f'code/{page.label}/{number:02}'
        source = f'{stem}.{ext}'
        line_count = max(1, len(raw.split('\n')))
        block = {'page': page.path, 'ordinal': number, 'kind': cls(node),
                 'language': hint, 'source': source, 'sha256': write(source, raw),
                 'lines': line_count, 'rendered': source}
        self.blocks.append(block)
        self.counts[cls(node)] += 1
        size = min(9, line_count + 2)
        if hint == 'Terminal':
            return f'\n\\BookTerminal{{{source}}}{{{size}}}{{{line_count}}}\n'
        if hint not in LEXERS:
            return f'\n\\BookPlain{{{source}}}{{{size}}}{{{line_count}}}\n'
        tokens = [(kind, value) for _, kind, value in LEXERS[hint]().get_tokens_unprocessed(raw)]
        if ''.join(value for _, value in tokens) != raw:
            raise ValueError(f'{source}: syntax lexer changed code')
        styled = f'{stem}.pv'
        block['rendered'] = styled
        block['rendered_sha256'] = write(styled, format_tokens(tokens, self.syntax))
        numbers = 'numbers=left,xleftmargin=19pt' if len(raw.splitlines()) >= 12 else 'numbers=none'
        return f'\n\\BookSource{{{numbers}}}{{{styled}}}{{{size}}}{{{line_count}}}\n'

    def convert(self):
        write('config/syntax.generated.tex', self.syntax.get_style_defs() + '\n')
        toc = self.manifest['toc']
        planned = {entry['href']: entry for entry in toc}
        chapters, appendices = [], []
        current = None
        buffers = {}
        for page in self.pages.values():
            renderer = Renderer(self, page)
            kind = page.kind
            if kind == 'book':
                renderer.edition()
                self.record_page(page, 'frontmatter/copyright.tex')
                continue
            if kind == 'preface':
                output = f'frontmatter/{"preface" if page.path == "pr02.html" else "history"}.tex'
                write(output, renderer.page_text())
                self.record_page(page, output)
                continue
            if kind == 'part':
                part = page.label.removeprefix('pt').lstrip('0')
                directory = f'chapters/part{part}'
                output = f'{directory}/part.tex'
                chapters.append(output)
                write(output, renderer.page_text())
                self.record_page(page, output)
                continue
            if kind == 'chapter':
                current = f'{directory}/{page.label}.tex'
                chapters.append(current)
            elif kind == 'appendix':
                current = f'appendices/{page.label}.tex'
                appendices.append(current)
            elif kind == 'bibliography':
                current = 'references/bibliography.tex'
            elif kind == 'index':
                current = 'index/index.tex'
            elif kind != 'sect1':
                raise ValueError(f'Unexpected document root {kind} for {page.path}')
            if kind != 'sect1':
                buffers[current] = []
            buffers[current].append(renderer.page_text())
            self.record_page(page, current)
        for filename, chunks in buffers.items():
            write(filename, '\n'.join(chunks))
        for path, inputs in [('chapters/contents.tex', chapters), ('appendices/contents.tex', appendices)]:
            write(path, ''.join(f'\\input{{{x.removesuffix(".tex")}}}\n' for x in inputs))
        mapped = {item['html'].removeprefix('source-html/'): item for item in self.mapping}
        contents = [{**entry,
                     'tex': mapped[entry['href'].split('#')[0]]['tex'],
                     'label': self.target(self.pages['index.html'], entry['href'])} for entry in toc]
        missing_labels = [(e['href'], e['label']) for e in contents if e['label'] not in self.emitted_anchors]
        if missing_labels:
            raise ValueError(f'Unemitted TOC destinations: {missing_labels}')
        if len(planned) != len(contents):
            raise ValueError('Repeated TOC entries')
        return {'counts': self.counts, 'pages': self.mapping, 'contents': contents,
                'blocks': self.blocks, 'image_uses': dict(self.assets), 'anchors': len(self.emitted_anchors),
                'links': dict(self.links),
                'repaired_source_links': [
                    dict(page=p, href=h, resolution=r, fragment=f, count=n)
                    for (p, h, r, f), n in sorted(self.missing_links.items())]}


class Renderer:
    def __init__(self, book, page):
        self.book, self.page = book, page
        self.code_number = 0
        self.level = 'section'
        self.in_index = False
        self.inline_table = 0
        self.notes = {
            node.find('.//a').get('id'): node for node in page.root.iter('div') if cls(node) == 'footnote'
        }

    def anchor(self, node):
        if node.get('id'):
            return self.book.anchor(name(self.page, node.get('id')))
        return ''

    def children(self, node, text_filter=None):
        if text_filter is None:
            text_filter = technical_prose if self.page.path not in ('pr02.html', 'apb.html') else prose
        out = [text_filter(node.text)]
        for child in node:
            out.extend((self.render(child), text_filter(child.tail)))
        return ''.join(out)

    def link(self, node):
        anchor = self.anchor(node)
        href = node.get('href')
        if not href:
            return anchor + self.children(node)
        visible = self.children(node).strip()
        if not visible:
            return anchor
        target = self.book.target(self.page, href, txt(node))
        if target:
            self.book.links['internal'] += 1
            link = r'\hyperlink{' + target + '}{' + visible + '}'
            if self.in_index:
                link += r'（\pageref{' + target + '}）'
            return anchor + link
        self.book.links['external'] += 1
        href = quote(href, safe=":/?#[]@!$&'()*+,;=%._~-")
        href = href.replace('%', r'\%').replace('#', r'\#')
        if normalize(txt(node)) == node.get('href') and href.startswith(('https:', 'http:')):
            return anchor + r'\url{' + href + '}'
        return anchor + r'\href{' + href + '}{' + visible + '}'

    def footnote(self, node):
        if any(cls(a) == 'footnote' for a in node):
            ref = next(a for a in node if cls(a) == 'footnote')
            body = self.notes[ref.get('href').removeprefix('#')]
            number = txt(ref)
            p = body.find('p')
            backref = p.find('sup/a')
            text = (self.anchor(backref) +
                    r'\BookFootnoteBack{' + name(self.page, ref.get('id')) + '}' +
                    prose(p.find('sup').tail).lstrip())
            for child in list(p)[1:]:
                text += self.render(child) + prose(child.tail)
            text += ''.join(self.render(extra) for extra in list(body)[1:])
            self.book.counts['footnote'] += 1
            return self.anchor(ref) + f'\\footnote[{number}]{{{text.strip()}}}'
        return r'\textsuperscript{' + self.children(node) + '}'

    def heading(self, node, command, pattern=r'(?!)', suffix=''):
        title = []
        anchors = []
        pending = True
        for element in [node, *node]:
            fragment = element.text if element is node else element.tail
            if element is not node:
                if element.tag == 'a' and not element.get('href'):
                    anchors.append(self.anchor(element))
                else:
                    title.append(self.render(element))
                    pending = False
            if pending:
                fragment = re.sub(pattern, '', (fragment or '').lstrip())
                pending = not fragment
            title.append(prose(fragment))
        title = ''.join(title).strip()
        return f'\n\\{command}{{{title}}}\n{suffix}{"".join(anchors)}%\n'

    def list(self, node):
        if node.tag == 'dl':
            out = ['\n\\begin{description}\n']
            for child in node:
                if child.tag == 'dt':
                    out.append(r'\item[{' + self.children(child).strip() + '}]\n')
                elif child.tag == 'dd':
                    out.append(self.children(child))
            return ''.join(out) + '\n\\end{description}\n'
        env = 'enumerate' if node.tag == 'ol' else 'itemize'
        label = r'[label=\alph*.]' if node.get('type') == 'a' else ''
        return f'\n\\begin{{{env}}}{label}\n{self.children(node)}\\end{{{env}}}\n'

    def image(self, node, display=False):
        src = node.get('src')
        self.book.assets[src] += 1
        if src.endswith('.gif'):
            src = 'images/derived/' + Path(src).name + '.png'
        if not (ROOT / src).is_file():
            raise FileNotFoundError(src)
        if display:
            from PIL import Image
            with Image.open(ROOT / src) as image:
                width = min(.96, max(.12, image.width / 660))
            return f'\\BookImage{{{src}}}{{{width:.3f}}}'
        return r'\BookInlineImage{' + src + '}'

    def diagram_contents(self, node):
        content = []
        for child in node:
            if child.tag == 'img':
                content.append(self.image(child, display=True))
            elif child.tag == 'div' and not cls(child):
                content.append(self.diagram_contents(child))
            else:
                content.append(self.render(child))
            content.append(prose(child.tail))
        return ''.join(content)

    def caption_block(self, node):
        kind = cls(node)
        caption = only_direct(node, 'title')
        caption_text = self.children(caption.find('b'), prose).strip()
        # Match numbers in the plain source before removing the rendered prefix.
        m = CAPTION.match(normalize(txt(caption)))
        if not m:
            raise ValueError(f'{self.page.path}: malformed caption: {txt(caption)}')
        title = re.sub(CAPTION.pattern, '', caption_text)
        if title == caption_text:
            raise ValueError(f'{self.page.path}: cannot remove caption prefix: {caption_text}')
        anchors = ''.join(self.anchor(a) for a in node if a.tag == 'a')
        body = only_direct(node, kind + '-contents')
        self.book.counts[kind] += 1
        if kind == 'figure':
            # The anchor precedes the complete graphic so jumping never hides the image.
            return '\n\\BookFigure{' + title + '}{' + self.diagram_contents(body) + '}{' + anchors + '}\n'
        if kind == 'table':
            self.inline_table += 1
            cap = r'\BookTableTitle{' + title + r'}\BookTableLabel{' + anchors + '}'
            result = render_table(body.find('table'), self.children, caption=cap)
            self.inline_table -= 1
            return '\n' + result
        if (len(body) == 1 and body[0].tag == 'div' and not cls(body[0])
                and len(body[0]) == 1 and body[0][0].tag == 'img'):
            img_tex = self.image(body[0][0], display=True)
            return (f'\n\\begin{{BookExampleGraphic}}\n'
                    f'\\BookExampleTitle{{{title}}}{anchors}\n'
                    f'{img_tex}\n\\end{{BookExampleGraphic}}\n')
        return f'\n\\BookExampleTitle{{{title}}}{anchors}\n{self.children(body)}'

    def literal_layout(self, node):
        out = []
        for paragraph in node:
            if self.page.path == 'apb.html':
                license_lines = [''.join(line) for line in source_lines(paragraph, scripts=True)]
                for line in license_lines:
                    text = normalize(line)
                    if not text:
                        continue
                    if re.match(r'^\d+\. [A-Z]', text) or text.startswith('ADDENDUM:'):
                        out.append(r'\BookLicenseHeading{' + escape(text) + '}\n')
                    else:
                        out.append(escape(text) + '\n\n')
                self.book.counts['license_nonempty_lines'] += sum(bool(x.strip()) for x in license_lines)
                continue
            source = [''.join(line) for line in source_lines(paragraph, scripts=True)]
            math = [display_math(line) for line in source]
            if len(math) == 1 and math[0]:
                out.append('\n\\[' + math[0] + '\\]\n')
                self.book.counts['display_math'] += 1
                continue
            if self.page.path in ('ch04s03.html', 'ch05s03.html', 'expr.expression.html'):
                # These known layouts have only arithmetic/logic symbols and no prose.
                exact = bool(source[0].startswith(('¬¬x=x', '0!\xa0=', 'fib(0)=1', '⌊59/60⌋')))
                if exact:
                    for line in source:
                        value = line.strip().replace('\u00a0', '')
                        if value:
                            value = value.replace('¬', r'\lnot ').replace('·', r'\cdot ')
                            for char, tex in [('⌊', r'\lfloor '), ('⌋', r'\rfloor '),
                                              ('⌈', r'\lceil '), ('⌉', r'\rceil ')]:
                                value = value.replace(char, tex)
                            if value.startswith('fib'):
                                value = value.replace('fib', r'\operatorname{fib}')
                            out.append(r'\BookMathLine{' + value + '}\n')
                            self.book.counts['display_math'] += 1
                        else:
                            out.append('\\smallskip\n')
                    continue
            lines = []
            for line in source_lines(paragraph):
                rendered = ''.join(self.layout_spaces(part) if isinstance(part, str) else self.render(part) for part in line)
                lines.append(r'\BookLiteralLine{' + rendered + '}\n')
            out.append('\n\\begin{BookLiteral}\n' + ''.join(lines) + '\\end{BookLiteral}\n')
        if self.page.path == 'apb.html':
            return '\n\\begin{BookLicense}\n' + ''.join(out) + '\\end{BookLicense}\n'
        return ''.join(out)

    @staticmethod
    def layout_spaces(text):
        pieces = re.split(r'([ \u00a0]{2,})', text.replace('\n', ''))
        return ''.join(r'\hspace*{' + f'{len(piece)*.32:.2f}em' + '}' if i % 2
                       else prose(piece) for i, piece in enumerate(pieces))

    def render(self, node):
        tag, kind = node.tag, cls(node)
        if tag == 'a':
            return self.link(node)
        if tag == 'pre':
            self.code_number += 1
            return self.book.source_block(self.page, node, self.code_number)
        if tag == 'p':
            if self.page.path == 'pr02.html' and not len(node) and (node.text or '').startswith('感谢热心网友'):
                start = 0
                content = []
                for match in ADDRESS.finditer(node.text):
                    content += [prose(node.text[start:match.start()]),
                                r'\BookAddress{' + match[0] + '}']
                    start = match.end()
                content.append(prose(node.text[start:]))
                return '\n\n' + ''.join(content) + '\n\n'
            return '\n\n' + self.children(node).strip() + '\n\n'
        if tag in ('ol', 'ul', 'dl'):
            return self.list(node)
        if tag == 'li':
            return '\n\\item ' + self.children(node).strip() + '\n'
        if tag == 'table':
            self.inline_table += 1
            result = render_table(node, self.children, nested=self.inline_table > 1)
            self.inline_table -= 1
            return result
        if tag == 'code':
            if len(node):
                return r'\BookCode{' + self.children(node) + '}'
            return r'\BookCode{' + code_text(normalize(txt(node))) + '}'
        if tag in ('em', 'i', 'b'):
            command = 'textbf' if tag == 'b' else 'emph'
            return f'\\{command}{{{self.children(node)}}}'
        if tag == 'sup':
            return self.footnote(node)
        if tag == 'sub':
            return r'\textsubscript{' + self.children(node) + '}'
        if tag == 'img':
            return self.image(node)
        if tag == 'br':
            return '' if kind.endswith('-break') else r'\newline{}'
        if tag in ('span', 'abbr'):
            return self.children(node)
        if tag == 'div':
            if kind in ('toc', 'titlepage', 'footnotes'):
                return ''
            if kind in ('sect2', 'simplesect'):
                level = 'subsection' if kind == 'sect2' else self.level + '*'
                was = self.level
                if kind == 'sect2':
                    self.level = 'subsubsection'
                self.book.counts[kind] += 1
                title = self.heading(title_of(node), level, NUMBER.get(kind, r'(?!)'))
                body = self.children(node)
                self.level = was
                return title + body
            if kind in ('example', 'figure', 'table'):
                return self.caption_block(node)
            if kind == 'literallayout':
                self.book.counts[kind] += 1
                return self.literal_layout(node)
            if kind == 'note':
                self.book.counts[kind] += 1
                return '\n\\begin{BookNote}\n' + self.children(node) + '\\end{BookNote}\n'
            if kind == 'biblioentry':
                self.book.counts[kind] += 1
                return '\n\\begin{BookBibliographyEntry}\n' + self.children(node) + '\\end{BookBibliographyEntry}\n'
            if kind == 'index':
                self.in_index = True
                def index_entry(term):
                    self.book.counts['index_entries'] += 1
                    return self.children(term)
                text = render_index(node, index_entry)
                self.in_index = False
                return text
            if (kind == '' and len(node) == 1 and node[0].tag == 'img'
                    and not (node[0].tail or '').strip()):
                return '\n\\BookDisplayImage{' + self.image(node[0], display=True) + '}\n'
            if kind in ('', 'itemizedlist', 'orderedlist', 'variablelist', 'legalnotice'):
                return self.children(node)
        if HEADING.fullmatch(tag) and kind == 'title':
            return r'\BookNoteTitle{' + self.children(node).strip() + '}\n'
        raise ValueError(f'{self.page.path}: unhandled element {tag=} {kind=} {node.attrib}')

    def navigation(self):
        nav = self.page.record['nav']
        items = []
        for key, title in [('prev', '上一页'), ('up', '上一级'), ('start', '起始页'), ('next', '下一页')]:
            if nav.get(key):
                link = self.book.target(self.page, nav[key])
                if link:
                    items.append(r'\hyperlink{' + link + '}{' + title + '}')
        return r'\BookNav{' + r'\enspace\textperiodcentered\enspace '.join(items) + '}\n' if items else ''

    def page_text(self):
        kind = self.page.kind
        if kind == 'sect1':
            level = 'section'
            self.level = 'subsection'
        elif kind in ('preface', 'bibliography', 'index'):
            level = 'BookFrontHeading'
        else:
            level = 'chapter' if kind == 'appendix' else kind
        self.book.counts[kind] += 1
        if kind == 'part':
            heading = title_of(self.page.root)
            title = self.heading(heading, 'BookPart', NUMBER[kind])
            title = title.removesuffix('%\n').strip()
            command, anchors = title.split('\n', 1)
            anchors = self.book.anchor(name(self.page)) + anchors
            return f'{command}{{{anchors}}}{{{self.navigation()}}}\n'
        return (f'\n% {self.page.record["url"]}\n' +
                self.heading(title_of(self.page.root), level, NUMBER.get(kind, r'(?!)'),
                             self.book.anchor(name(self.page))) +
                self.children(self.page.root).strip() + '\n\n' + self.navigation())

    def edition(self):
        titlepage = only_direct(self.page.root, 'titlepage')
        author = next(a for a in titlepage.iter('div') if cls(a) == 'author')
        legal = next(a for a in titlepage.iter('div') if cls(a) == 'legalnotice')
        copyright = next(a for a in titlepage.iter('p') if cls(a) == 'copyright')
        pubdate = next(a for a in titlepage.iter('p') if cls(a) == 'pubdate')
        revisions = next(a for a in titlepage.iter('div') if cls(a) == 'revhistory').find('table')
        self.book.counts['book'] += 1
        credits = [
            r'\BookFrontHeading{版权及许可证声明}',
            self.book.anchor(name(self.page)),
            ''.join(self.anchor(a) for a in title_of(self.page.root).iter('a')),
            r'\noindent 原书\quad \OriginalTitle\par',
            r'\noindent 原作者\quad ' + prose(author.findtext('.//span[@class="firstname"]')) + r'\par',
            r'\noindent 原出版机构\quad ' + prose(author.findtext('.//span[@class="orgname"]')) + r'\par',
            r'\noindent 原书联系信息\quad ' + self.render(author.find('code')) + r'\par',
            r'\noindent 原书日期\quad ' + self.children(pubdate) + r'\par',
            '\n' + self.children(copyright) + '\n',
            r'Copyright © \EditionYear\ \EditionRightsHolder\ （本版排版与整理）\par',
            r'\medskip\noindent 原始许可证声明\par',
            self.render(legal),
            r'本排版整理版以 GNU Free Documentation License 第 1.3 版或自由软件基金会发布的任何后续版本发布。不可变章节为「前言」，无 Front-Cover Texts 和 Back-Cover Texts。许可证全文见' +
            r'\hyperlink{db.apb}{附录 B}。' + '\n\n',
            r'原书网址\quad\url{https://akaedu.github.io/book/}' + '\n\n',
            r'本版的可编辑副本随附于 \LaTeX{} 源码工程。' + '\n',
        ]
        write('frontmatter/copyright.tex', '\n'.join(credits))
        rows = revisions.findall('tr')
        original_title = normalize(txt(rows[0]))
        history = [rf'\BookFrontHeading{{{escape(original_title)}}}', '']
        for row in rows[1:]:
            fields = row.findall('td')
            if len(fields) > 1:
                history.append(r'\noindent\textbf{' + self.children(fields[0]).strip() +
                               r'}\hfill ' + self.children(fields[1]).strip() + r'\par')
            else:
                history.append(self.children(fields[0]).strip() + '\n')
        history.extend([
            r'\medskip\noindent\textbf{LaTeX 排版整理版 \EditionVersion}\hfill \EditionDate\par',
            r'《\EditionTitle》。原作者宋劲杉，整理者\EditionEditor，发布者\EditionPublisher。',
            r'据原书在线版本（宋劲杉，北京亚嵌教育研究中心，2009）转换排版。',
            self.navigation(),
        ])
        write('frontmatter/revisions.tex', '\n'.join(history) + '\n')


def main():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding='utf-8'))
    result = Book(manifest, load_pages(manifest)).convert()
    write('manifest/conversion.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['counts'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
