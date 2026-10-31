import json,glob,re,unicodedata,collections,sys
MESES={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
def norm(s):
    s=unicodedata.normalize('NFD',(s or '').lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s).split())
CONN={'de','del','la','las','los','y','i','e','da','dos','das','van','von','san','santa','d'}
STOPW={'Presidente','Presidenta','Director','Directora','Subsecretario','Subsecretaria','Secretario','Secretaria','Ministro','Ministra','Delegado','Delegada','Gobernador','Gobernadora','Vicepresidente','Vicepresidenta','Consejero','Consejera','Vocal','Embajador','Embajadora','Comisionado','Comisionada','Interventor','Interventora','Abogado','Abogada','Fiscal','Jefe','Jefa','Teniente','General','Coronel','Almirante','Alto','Alta','Inspector','Inspectora','Gerente','Adjunto','Adjunta','Magistrado','Magistrada','Capitán','Contralmirante','Vicealmirante','Representante','Comisario','Comisaria','Defensor','Defensora','Rector','Decano','Miembro','Consejeros','Ministros','Excelentísimo','Excmo','Doctor'}
OCRFIX=[(r'\bFemando\b','Fernando'),(r'\bMartln\b','Martín'),(r'\bFemández\b','Fernández'),(r'\bHemández\b','Hernández'),(r'\bBemardo\b','Bernardo')]
def take_name(s):
    for a,b in OCRFIX: s=re.sub(a,b,s)
    toks=s.split(' '); out=[]
    for i,t in enumerate(toks):
        w=t.strip(',.;:»«"()')
        if not w: break
        if w in STOPW and out: break
        def nxtcap(j):
            while j<len(toks) and toks[j].strip(',.;:').lower() in CONN: j+=1
            return j<len(toks) and toks[j][:1].isupper()
        if w[0].isupper() or (w.lower() in CONN and out and nxtcap(i+1)):
            out.append(w)
            if t[-1:] in ',.;:)': break
        else: break
    while out and out[-1].lower() in CONN: out.pop()
    return ' '.join(out)
NAME_RE=re.compile(r'\b(don|doña|Don|Doña|D\.|Dª|D\.ª)[\s\-]+')
def rd_date(t):
    m=re.match(r'(Real Decreto|Decreto)\s+(\d+)\s*/\s*(\d{4}),?\s+de\s+(\d{1,2})\s+de\s+(\w+)',t)
    if not m: return None,None
    n,y,d,mes=m.group(2),int(m.group(3)),int(m.group(4)),MESES.get(m.group(5).lower())
    if not mes: return m.group(1)+' '+n+'/'+str(y),None
    return m.group(1)+' '+n+'/'+str(y), f'{y:04d}-{mes:02d}-{d:02d}'
def split_title(t):
    """devolve (kind, [(nome, sexo)], cargo) ou None"""
    m=re.search(r',?\s+por (?:el|la) que\s+(.*)$',t)
    if not m: return None
    b=m.group(1).strip().rstrip('.')
    low=b.lower()
    if re.search(r'\bcese|\bcesa\b|\bcesan\b',low): kind='c'
    elif re.search(r'\bnombra|\bnombramiento|\bdesigna',low): kind='n'
    else: return None
    names=[]
    for mm in NAME_RE.finditer(b):
        nm=take_name(b[mm.end():])
        if nm: names.append((nm,'M' if mm.group(1).lower().startswith('doñ') or 'ª' in mm.group(1) else 'H',mm.start(),mm.end()+len(nm)))
    if len(names)!=1: return (kind,names,None,b)
    nm,sx,a,z=names[0]
    rest=(b[:a]+' § '+b[z:]).strip()
    # quitar verbos e conectores
    c=rest
    c=re.sub(r'^(se\s+)?(dispone|declara|acuerda)\s+(que\s+)?','',c)
    c=re.sub(r'^(el\s+)?(cese|nombramiento|designación)\s*,?\s*(a petición propia,?\s*|por pase a otro destino,?\s*|por jubilación,?\s*)?','',c)
    c=re.sub(r'^(se\s+)?(nombra|designa|cesa|cese|nombran)\s+','',c)
    c=re.sub(r'^(como|en el cargo de|en su cargo de|en el puesto de|de)\s+','',c)
    # partes ao redor do nome
    parts=[p.strip(' ,') for p in c.split('§')]
    def clean(p):
        p=re.sub(r'^(a|de|al|en)\s*$','',p.strip())
        p=re.sub(r'^(a|de)\s+$','',p)
        p=re.sub(r'\s+(a|de|al)$','',p)
        p=re.sub(r'^(,?\s*)?(como|en el cargo de|en su cargo de|en el puesto de|cese como|cese en el cargo de|cesa como|cesa en el cargo de|que cese en el cargo de|que cese como)\s+','',p)
        p=re.sub(r'^(se\s+)?(dispone|declara)\s+(el\s+)?cese\s+(como|en el cargo de|de)\s+','',p)
        p=re.sub(r'^(cese|cesa|nombra)\s+(como|en el cargo de)?\s*','',p)
        p=re.sub(r',?\s*(a petición propia|por pase a otro destino|por jubilación|por fallecimiento|con carácter interino|con efectos de.*|agradeciéndole.*|en funciones|por pase a la situación.*|por renuncia|por cese de.*|por haber sido.*|por nombramiento.*|por cambio de destino|por pase a la reserva.*)$','',p,flags=re.I)
        p=re.sub(r'\s+(el|al|del)\s+(Teniente General|General|Almirante|Vicealmirante|Contralmirante|Coronel|Teniente Coronel|Embajador|excelentísimo|Excelentísimo)\b.*$','',p)
        p=re.sub(r'^(al|a la|a los)\s+','',p)
        return p.strip(' ,.')
    ps=[clean(p) for p in parts]
    ps=[p for p in ps if p and not re.fullmatch(r'(a|de|del|al|en|que|como)',p)]
    cargo=max(ps,key=len) if ps else ''
    cargo=re.sub(r'\s+(al|a la)\s+(Teniente General|General|Almirante|Coronel|Contralmirante|Vicealmirante|Embajador|Ministro Plenipotenciario|Magistrado)\b.*$','',cargo)
    return (kind,[(nm,sx)],cargo,b)
if __name__=='__main__':
    yr=sys.argv[1]
    for f in sorted(glob.glob(f'raw/{yr}/*.json')):
        for it in json.load(open(f)) or []:
            t=it['t'] or ''
            if not re.match(r'(Real )?Decreto',t): continue
            r=split_title(t)
            print(f[-13:-5],'|',r[0] if r else '-', '|', (r[1][0][0] if r and r[1] and len(r[1])==1 else r[1] if r else ''),'|',r[2] if r else '','||',t[:160])
