import re,sys,json,unicodedata
PROVS=['Almería','Cádiz','Córdoba','Granada','Huelva','Jaén','Málaga','Sevilla']
NOISE=re.compile(r'Depósito Legal|eboja|^\s*BOJA\s*$|página \d|Número \d|Boletín Oficial|^\s*\d{8}\s*$|ORGANISMO:|CONSEJERÍA, ENTIDAD|Secretaría General Técnica|ANEXO|A DM I NI|Extraordinario núm|Hoja \d|^\s*\d+ de \d+\s*$|Publicación de candidaturas|Elecciones al Parlamento de Andalucía 20|JUNTA ELECTORAL PROVINCIAL|INSER1|SECCIÓN, SUBSECCIÓN|SUMARIO|TEXTO:|C O NS E J|PRIMERA PÁGINA')
def parse(path):
    L=open(path,encoding='utf8').read().split('\n')
    out=[]; prov=None; cur=None; pend=False; sup=False
    for ln in L:
        if not ln.strip() or NOISE.search(ln): continue
        m=re.search(r'Circunscripción electoral:\s*(\S.*\S)',ln)
        if m: prov=m.group(1).strip(); assert prov in PROVS,prov; continue
        m=re.search(r'Candidatura núm\.:\s*(\d+)\.\s*(.*\S)',ln)
        if m:
            cur={'pr':prov,'n':int(m.group(1)),'tit':m.group(2),'c':[],'s':[]}; out.append(cur); pend=True; sup=False; continue
        if cur is None: continue
        if 'NO PROCLAMADA' in ln: cur['np']=True; pend=False; continue
        if re.match(r'^\s*Suplentes\s*$',ln): sup=True; pend=False; continue
        m=re.match(r"^\s*(\d+)\.\s+(.*\S)\s*$",ln)
        if m:
            pend=False
            (cur['s'] if sup else cur['c']).append((int(m.group(1)),m.group(2))); continue
        if pend: cur['tit']+=' '+ln.strip(); continue
        print('??',repr(ln),file=sys.stderr)
    return out
def splitname(raw):
    s=raw.strip()
    s=s.replace("'RxD","Doña ")
    sx=None
    m=re.match(r'^(?:(Doña|Don|DOÑA|DON)\s+)+',s)
    if m:
        hs=re.findall(r'(Doña|Don|DOÑA|DON)',m.group(0)); sx='M' if hs[-1].lower()=='doña' else 'H'; s=s[m.end():]
    ind=False; pi=None
    m=re.search(r'\s*\(([^)]*)\)\s*$',s)
    if m:
        t=m.group(1).strip()
        if t.lower() in('independiente','independent'): ind=True
        else: pi=t
        s=s[:m.start()]
    return s.strip(),sx,ind,pi
if __name__=='__main__':
    for f in sys.argv[1:]:
        C=parse(f)
        print(f,len(C),sum(len(c['c'])+len(c['s']) for c in C))
        for c in C:
            if c.get('np'): print('  NP',c['pr'],c['tit']); continue
            o=[x[0] for x in c['c']]; so=[x[0] for x in c['s']]
            if o!=list(range(1,len(o)+1)) or so!=list(range(1,len(so)+1)): print('  ORD',c['pr'],c['tit'],o,so)
            for _,r in c['c']+c['s']:
                n,sx,ind,pi=splitname(r)
                if sx is None: print('  NAME',c['pr'],c['tit'][:30],repr(r))
