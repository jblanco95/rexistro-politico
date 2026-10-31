import json,re,os,subprocess,urllib.request,time,sys,glob
from parse import take_name,NAME_RE,rd_date
os.makedirs('docs',exist_ok=True)
def fetch(url,fn):
    if os.path.exists(fn): return open(fn,'rb').read()
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'rexistro-politico (investigacion)'}),timeout=90) as r: b=r.read()
            open(fn,'wb').write(b); return b
        except Exception: time.sleep(2**k)
    return None
def doc_text(bid,wide=False):
    x=fetch(f'https://www.boe.es/diario_boe/xml.php?id={bid}',f'docs/{bid}.xml')
    if not x: return None
    x=x.decode('utf8','replace')
    m=re.search(r'<texto>(.*?)</texto>',x,re.S)
    if m and len(re.sub('<[^>]+>','',m.group(1)).strip())>40:
        return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',m.group(1)))
    u=re.search(r'<url_pdf>([^<]+)</url_pdf>',x); num=re.search(r'<numero_oficial>([^<]+)</numero_oficial>',x)
    if not u: return None
    pdf=fetch(u.group(1),f'docs/{bid}.pdf')
    if not pdf: return None
    t=subprocess.run(['pdftotext',f'docs/{bid}.pdf','-'],capture_output=True,text=True).stdout
    t=re.sub(r'\u00ad\s*\n(?=[A-ZÁÉÍÓÚÑ])','-',t)
    t=t.replace('\u00ad\n','').replace('\u00ad','')
    t=re.sub(r'-\n(?=[A-ZÁÉÍÓÚÑ])','-',t).replace('-\n','')
    t=re.sub(r'\s+',' ',t)
    if num:
        mm=re.search(r'(?:DECRETO|Decreto)\s+'+re.escape(num.group(1)),t); i=mm.start() if mm else t.find(num.group(1))
        if i>=0:
            nx=re.search(r'(REAL DECRETO|ORDEN|RESOLUCI[OÓ]N|Real Decreto \d+/\d{4}, de \d+ de \w+, por el)',t[i+40:])
            t=t[i:(i+40+nx.start() if nx and not wide else i+5000)]
    return t
CW=re.compile(r'\b(Ministr[oa]|Vicepresident[ea]|Secretari[oa]|Subsecretari[oa]|Director[a]?|Delegad[oa]|Gobernador[a]?|President[ea]|Interventor|Fiscal|Comisionad[oa])\b')
def ccl(p,side):
    p=p.strip()
    if ':' in p and side=='b': p=p.split(':')[-1]
    if side=='b': p=re.sub(r'^.*\b[A-ZÁÉÍÓÚÑ]{4,}\b\.?\s+(?=[A-ZÁÉÍÓÚ][a-záéíóú])','',p.strip())
    p=re.sub(r'\b\d{3,6}\b','',p)
    p=re.sub(r'^[\s,;.]*((y|e)\s+)?','',p)
    p=re.sub(r'^(como|para el cargo de|para el de|en el cargo de|en sus respectivos cargos|el cese de|cese de|de|a)\s+','',p)
    p=re.sub(r'^(como|para el cargo de|para el de|en el cargo de)\s+','',p)
    p=re.sub(r'[\s,;]+(y|e)(\s+(a|de))?\s*$','',p)
    p=re.sub(r'[\s,;]+(a|de|como)\s*$','',p)
    p=re.sub(r',?\s*(agradeci[ée]ndo.*|por pase a otro destino.*|a petición propia.*|con efectos.*)$','',p)
    p=re.sub(r'\s+(al|el)\s+(Teniente General|General|Almirante|Vicealmirante|Contralmirante|Coronel)\b.*$','',p)
    return p.strip(' ,.;:')
def parse_body(t,title=''):
    m=re.search(r'vengo en (nombrar|disponer|designar|declarar)\s*:?\s*(.*)',t,re.I)
    body=m.group(2) if m else t
    body=re.sub(r'Dado en [^.]*?(mil novecientos|dos mil)[a-zé ]*\.?','',body)
    ms=[(mm,take_name(body[mm.end():])) for mm in NAME_RE.finditer(body)]
    ms=[(mm,nm) for mm,nm in ms if nm]
    if not ms: return []
    spans=[(mm.start(),mm.end()+len(nm),nm,'M' if mm.group(1).lower().startswith('doñ') else 'H') for mm,nm in ms]
    bef=[body[(spans[i-1][1] if i else 0):sp[0]] for i,sp in enumerate(spans)]
    aft=[body[sp[1]:(spans[i+1][0] if i+1<len(spans) else len(body))] for i,sp in enumerate(spans)]
    nb=sum(1 for x in bef if CW.search(x.split(';')[-1] if ';' in x else x)); na=sum(1 for x in aft if CW.search(x))
    side='a' if na>nb else 'b'
    gc=re.search(r'Gobernadores? civiles?',title,re.I)
    if gc:
        eb=sum(1 for x in bef if re.search(r'\b(De|de|Del|del) [A-ZÁÉÍÓÚ][^,;:]{1,30}[,:]?\s*(a\s*)?$',x.strip()))
        ea=sum(1 for x in aft if re.match(r'^[\s,.;]*(De|de|Del|del) [A-ZÁÉÍÓÚ]',x) and not re.search(r'\b(De|de|Del|del) [A-ZÁÉÍÓÚ][^,;:]{1,30}[,:]?\s*(a\s*)?$',x.strip()))
        side='b' if eb>=ea else 'a'
    out=[]
    for i,(a,z,nm,sx) in enumerate(spans):
        c=ccl(aft[i] if side=='a' else (bef[i].split(';')[-1]),side)
        if side=='a': c=re.split(r';',c)[0].strip(' ,.')
        if gc and re.match(r'^(De|de|Del|del)\s+',c) and not CW.search(c): c='Gobernador civil de la provincia '+c[0].lower()+c[1:]
        if c and len(c)<220: out.append((nm,sx,c[:1].upper()+c[1:]))
    return out
if __name__=='__main__':
    for bid in sys.argv[1:]:
        t=doc_text(bid); print(bid, (t or '')[:200]); print(parse_body(t or ''))
