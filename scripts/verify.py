#!/usr/bin/env python3
"""Offline consistency checks against the unmodified source snapshot."""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json, re, sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
source = json.loads((ROOT/'manifest/source.json').read_text())
conversion = json.loads((ROOT/'manifest/conversion.json').read_text())
errors = []
def require(ok, message):
    if not ok: errors.append(message)
def read(path): return (ROOT/path).read_bytes()
def digest(data): return sha256(data).hexdigest()
def document(path):
    tree = ET.fromstring(read(path))
    for node in tree.iter(): node.tag = node.tag.rsplit('}', 1)[-1]
    return tree


def tex_visible(tex):
    """Interpret only known preface commands, retaining their visible arguments."""
    single={'&':'&','%':'%','$':'$','#':'#','_':'_','{':'{','}':'}'}
    wrappers={'BookFrontHeading','section','subsection','BookCode','BookAddress',
              'emph','textit','textbf','texttt','textnormal','textrm','textsf',
              'mbox','BookQuote','href','hyperlink'}
    discard={'BookAnchor','BookNav','label','begin','end'}
    two_args={'href','hyperlink'}
    spacing={'item','noindent','par','BookSplit','relax','enspace','textperiodcentered'}
    chars={'textbackslash':'\\','textasciitilde':'~','textasciicircum':'^',
           'BookQuoteChar':'"'}
    def parse(i, stop=False):
        out=[]
        while i<len(tex):
            c=tex[i]
            if c=='}' and stop: return ''.join(out),i+1
            if c=='%':
                j=tex.find('\n',i); i=len(tex) if j<0 else j+1; continue
            if c=='{':
                value,i=parse(i+1,True);out.append(value);continue
            if c!='\\': out.append(c);i+=1;continue
            i+=1
            if i>=len(tex): raise ValueError('trailing TeX escape')
            if not tex[i].isalpha():
                ch=tex[i];i+=1
                if ch in single: out.append(single[ch])
                elif ch in ' ,;!': out.append(' ')
                else: raise ValueError('unknown TeX escape '+repr(ch))
                continue
            start=i
            while i<len(tex) and tex[i].isalpha():i+=1
            name=tex[start:i]
            if i<len(tex) and tex[i]=='*':i+=1
            if name in spacing: continue
            if name in chars:
                out.append(chars[name])
                if tex[i:i+2]=='{}':i+=2
                continue
            if name not in wrappers|discard: raise ValueError('unknown preface command '+name)
            args=[]
            for _ in range(2 if name in two_args else 1):
                while i<len(tex) and tex[i].isspace():i+=1
                if i>=len(tex) or tex[i]!='{': raise ValueError('missing argument to '+name)
                value,i=parse(i+1,True);args.append(value)
            if name in wrappers: out.append(args[-1])
        if stop: raise ValueError('unclosed TeX group')
        return ''.join(out),i
    return parse(0)[0]


def compact_visible(text):
    # HTML and TeX introduce different structural whitespace around blocks.
    return ''.join(text.split())

def check():
    pages = source['pages']; mapped = conversion['pages']; toc = source['toc']; contents = conversion['contents']
    require(len(pages)==219, f'expected 219 source pages, got {len(pages)}')
    require(len(toc)==342, f'expected 342 TOC entries, got {len(toc)}')
    require([p['url'] for p in pages]==[p['url'] for p in mapped], 'page mapping differs from source order')
    require([{k:x[k] for k in ('href','title','kind','depth')} for x in contents]==toc, 'TOC entries differ from source or order')
    for item in pages + source['resources']:
        path=item['file']
        if not (ROOT/path).is_file(): errors.append(f'missing source {path}'); continue
        require(digest(read(path)) == item['sha256'], f'source SHA mismatch {path}')
    docs={p['path']:document(p['file']) for p in pages if (ROOT/p['file']).is_file()}
    output_cache={}
    for p in mapped:
        f=ROOT/p['tex']
        if not f.is_file(): errors.append(f'missing mapped TeX {p["tex"]}'); continue
        output_cache[p['tex']]=f.read_text()
        require('\\BookAnchor{'+p['label']+'}' in output_cache[p['tex']], f'page anchor absent: {p["html"]}')
    for entry in contents:
        require('\\BookAnchor{'+entry['label']+'}' in output_cache.get(entry['tex'],''), f'TOC anchor absent: {entry["href"]}')
    blocks=defaultdict(list)
    for b in conversion['blocks']: blocks[b['page']].append(b)
    total=0
    for path,doc in docs.items():
        found=[n for n in doc.iter('pre') if n.get('class') in ('programlisting','screen')]
        recorded=blocks[path]
        require(len(found)==len(recorded),f'{path}: source has {len(found)} literal blocks, conversion records {len(recorded)}')
        remaining=Counter((n.get('class'), ''.join(n.itertext()).encode()) for n in found)
        for i,b in enumerate(recorded,1):
            target=ROOT/b['source']
            require(b['ordinal']==i,f'{path}: literal block ordinal {i} mismatch')
            if not target.is_file(): errors.append(f'missing block {b["source"]}'); continue
            actual=target.read_bytes()
            require(digest(actual)==b['sha256'],f'literal block SHA mismatch: {b["source"]}')
            key=(b['kind'],actual)
            require(remaining[key]>0,f'literal block differs from source: {b["source"]}')
            remaining[key]-=1
            tex=next((x['tex'] for x in mapped if x['html']=='source-html/'+path),None)
            rendered = b['rendered']
            require(output_cache.get(tex, '').count('{' + rendered + '}') == 1,
                    f'expected one TeX reference to {rendered}')
            if 'rendered_sha256' in b:
                require((ROOT / rendered).is_file() and digest(read(rendered)) == b['rendered_sha256'],
                        f'highlighted block SHA mismatch: {rendered}')
            total+=1
    require(total==len(conversion['blocks']), 'unmatched block records')
    structure=Counter()
    def walk(node):
        kind=node.get('class','')
        if kind in ('toc','navheader','navfooter','footnotes'): return
        if node.tag=='div': structure[kind]+=1
        for child in node: walk(child)
    for doc in docs.values(): walk(doc)
    for kind in ('sect2','simplesect','table','figure','example','biblioentry','note'):
        require(structure[kind]==conversion['counts'][kind],f'{kind} structure mismatch: source {structure[kind]} vs conversion {conversion["counts"][kind]}')
    index=docs['ix01.html']; index_dt=sum(1 for e in index.iter('dt'))
    require(index_dt==conversion['counts']['index_entries'],f'index entry mismatch: {index_dt}')
    require((ROOT/'index/index.tex').read_text().count(r'\hangindent=1em')==index_dt,'index TeX entry count differs')
    # Compare the complete invariant preface (headings, paragraphs, list text,
    # inline formatting and visible links), not a sample of long fragments.
    from convert import source_lines, normalize, escape
    preface_div=next(e for e in docs['pr02.html'].iter('div') if e.get('class')=='preface')
    expected=compact_visible(''.join(preface_div.itertext()))
    try:
        actual=compact_visible(tex_visible((ROOT/'frontmatter/preface.tex').read_text()))
        if expected!=actual:
            i=next((j for j,(a,b) in enumerate(zip(expected,actual)) if a!=b),min(len(expected),len(actual)))
            errors.append(f'preface visible text differs at character {i}: source={expected[max(0,i-20):i+40]!r}, TeX={actual[max(0,i-20):i+40]!r}')
    except ValueError as exc:
        errors.append(f'preface TeX cannot be verified: {exc}')
    tex='\n'.join(output_cache.values())
    for kind,macro in [('figure','BookFigure'),('table','BookTableTitle'),('example','BookExampleTitle')]:
        actual=tex.count('\\'+macro+'{'); expected=conversion['counts'][kind]
        require(actual==expected,f'{kind} captions: {actual} TeX, {expected} recorded')
    # Verify that every recorded image occurrence is included in output.
    for src,count in conversion['image_uses'].items():
        target=('images/derived/'+Path(src).name+'.png') if src.endswith('.gif') else src
        require((ROOT/target).is_file(),f'missing rendered image {target}')
        require(tex.count('{'+target+'}')==count,f'image usage mismatch {src}: {tex.count("{"+target+"}")} vs {count}')
    # Nonempty license lines are kept in order, with TeX escaping only.
    doc=docs['apb.html']; lines=[]
    for layout in doc.iter('div'):
        if layout.get('class')=='literallayout':
            for para in layout:
                lines.extend(normalize(''.join(line)) for line in source_lines(para,scripts=True) if normalize(''.join(line)))
    license_tex=(ROOT/'appendices/apb.tex').read_text(); pos=0
    for line in lines:
        wanted=escape(line); where=license_tex.find(wanted,pos)
        require(where>=0,f'GFDL line missing or reordered: {line[:70]}')
        if where>=0: pos=where+len(wanted)
    require(len(lines)==conversion['counts']['license_nonempty_lines'],f'GFDL lines mismatch: {len(lines)}')
    print(f'Checked {len(pages)} pages, {len(toc)} TOC entries, {total} literal blocks, {len(lines)} GFDL lines, {len(conversion["image_uses"])} image paths.')
    if errors:
        print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr)
        print(f'{len(errors)} errors',file=sys.stderr); return 1
    print('Offline consistency checks passed.'); return 0
if __name__=='__main__': sys.exit(check())
