#!/usr/bin/env python3
"""Mirror the public DocBook HTML and its referenced assets; never follow external links."""
import concurrent.futures as cf
import hashlib, json, re, time, urllib.parse, urllib.request, urllib.error, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='https://akaedu.github.io/book/'
NS={'h':'http://www.w3.org/1999/xhtml'}
def get(path):
    url=urllib.parse.urljoin(BASE,path)
    try:
        result=subprocess.run(['curl','-fsSL','--max-time','40','--retry','2','--proto-redir','=https','-w','\n%{url_effective}',url],capture_output=True,timeout=130)
        if result.returncode: return path,None,result.stderr.decode('utf-8','replace').strip()
        body, final=result.stdout.rsplit(b'\n',1)
        if not final.decode().startswith(BASE): return path,None,'redirect outside book: '+final.decode()
        return path,body,None
    except Exception as e: return path,None,str(e)

def local(ref,base):
    url=urllib.parse.urljoin(urllib.parse.urljoin(BASE,base),ref)
    p=urllib.parse.urlsplit(url)
    if not url.startswith(BASE): return None
    path=urllib.parse.unquote(p.path[len('/book/'):]) or 'index.html'
    if '..' in Path(path).parts: return None
    return path

def save(path,data):
    dest=ROOT/('images' if path.startswith('images/') else 'source-html')/(path[7:] if path.startswith('images/') else path)
    dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
    return str(dest.relative_to(ROOT))
def digest(b): return hashlib.sha256(b).hexdigest()
def tree(b): return ET.fromstring(b)
def text(e): return ' '.join(''.join(e.itertext()).split())

_,index,err=get('index.html')
if err: raise SystemExit(err)
save('index.html',index)
root=tree(index); toc=[]; seen={'index.html'}; ordered=[{'path':'index.html','url':BASE+'index.html','title':root.findtext('.//h:title',namespaces=NS),'kind':'book','depth':0}]
tocdiv=root.find('.//h:div[@class="toc"]',NS)
for dt in tocdiv.findall('.//h:dt',NS):
    a=dt.find('.//h:a',NS)
    if a is None: continue
    span=dt.find('./h:span',NS); kind=span.get('class','') if span is not None else ''
    href=a.get('href',''); path=local(href,'index.html')
    # DocBook semantic level, including part nesting and same-page sect2.
    depth={'preface':1,'part':1,'chapter':2,'appendix':1,'bibliography':1,'index':1,'sect1':3,'sect2':4,'sect3':5}.get(kind,1)
    item={'href':href,'title':text(a),'kind':kind,'depth':depth}; toc.append(item)
    if path and path not in seen:
        seen.add(path); ordered.append({'path':path,'url':urllib.parse.urljoin(BASE,path),'title':text(a),'kind':kind,'depth':depth})
print('TOC:',len(toc),'entries;',len(ordered),'pages',flush=True)
data={'index.html':index}; errors={}; pending=[p['path'] for p in ordered if p['path']!='index.html']; external=set(); refs={}; assets=set()
with cf.ThreadPoolExecutor(max_workers=12) as pool:
    while pending:
        batch=list(dict.fromkeys(x for x in pending if x not in data and x not in errors)); pending=[]
        if not batch: break
        for path,body,error in pool.map(get,batch):
            if error: errors[path]=error; print('FAILED',path,error,flush=True); continue
            data[path]=body; save(path,body)
            if path.lower().endswith(('.html','.htm')):
                try: doc=tree(body)
                except ET.ParseError as e: errors[path]='XML parse: '+str(e); continue
                for elem in doc.iter():
                    tag=elem.tag.rsplit('}',1)[-1]
                    for attr in ('href','src','data'):
                        ref=elem.get(attr)
                        if not ref or ref.startswith(('#','mailto:','javascript:')): continue
                        full=urllib.parse.urljoin(urllib.parse.urljoin(BASE,path),ref)
                        target=local(ref,path)
                        if target is None:
                            if urllib.parse.urlsplit(full).scheme in ('http','https'): external.add(full)
                            continue
                        refs.setdefault(path,[]).append(ref)
                        if tag=='a' and target.lower().endswith(('.html','.htm')):
                            if target not in seen:
                                seen.add(target); pending.append(target)
                                ordered.append({'path':target,'url':urllib.parse.urljoin(BASE,target),'title':'','kind':'linked','depth':0})
                        elif tag in ('img','object','script','source') or (tag=='link' and elem.get('rel')=='stylesheet'):
                            assets.add(target)
            elif path.lower().endswith('.css'):
                for ref in re.findall(r'url\([\'\"]?([^\)\'\"]+)',body.decode('utf-8','replace')):
                    target=local(ref,path)
                    if target: assets.add(target)
        pending.extend(x for x in assets if x not in data and x not in errors)
        print('downloaded',len(data),'errors',len(errors),'pending',len(pending),flush=True)
# Index references must also be checked (it was downloaded before the loop).
for p in ordered:
    if p['path'] in data:
        p['sha256']=digest(data[p['path']]); p['file']='source-html/'+p['path']
        try:
            doc=tree(data[p['path']]); p['document_title']=doc.findtext('.//h:title',namespaces=NS)
            p['nav']={e.get('rel'):e.get('href') for e in doc.findall('.//h:head/h:link',NS) if e.get('rel') in ('prev','next','up','start')}
        except ET.ParseError: pass
    else: p['error']=errors.get(p['path'],'not fetched')
mismatches=[]
for i,p in enumerate(ordered):
    for rel,j in [('prev',i-1),('next',i+1)]:
        actual=p.get('nav',{}).get(rel); expected=ordered[j]['path'] if 0<=j<len(ordered) else None
        if actual!=expected: mismatches.append({'path':p['path'],'rel':rel,'actual':actual,'expected':expected})
resources=[{'path':p,'url':urllib.parse.urljoin(BASE,p),'file':('images/'+p[7:] if p.startswith('images/') else 'source-html/'+p),'sha256':digest(data[p])} for p in sorted(assets) if p in data]
manifest={'base_url':BASE,'pages':ordered,'toc':toc,'resources':resources,'missing':[{'path':p,'error':e} for p,e in sorted(errors.items())],'external':sorted(external),'nav_mismatches':mismatches}
(ROOT/'manifest/source.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('DONE',len(ordered),'pages',len(resources),'resources',len(errors),'failures',len(mismatches),'nav mismatches',flush=True)
