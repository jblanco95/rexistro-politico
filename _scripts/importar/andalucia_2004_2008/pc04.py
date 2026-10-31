import re,sys,collections
PV={'ALMERIA':'Almería','CADIZ':'Cádiz','CORDOBA':'Córdoba','GRANADA':'Granada','HUELVA':'Huelva','JAEN':'Jaén','MALAGA':'Málaga','SEVILLA':'Sevilla'}
def isup(t):
    a=[c for c in t if c.isalpha()]; return a and sum(c.isupper() for c in a)/len(a)>0.75
def parse(path):
    L=open(path,encoding='utf8').read().replace('\t',' ').split('\n')
    out=[];prov=None;cur=None;sup=False;pend=False
    for ln in L:
        m=re.search(r'JUNTA ELECTORAL PROVINCIAL DE (\w+)',ln)
        if m and m.group(1) in PV: prov=PV[m.group(1)]; cur=None; continue
        if prov is None or not ln.strip(): continue
        if re.search(r'BOJA núm|Página núm',ln): continue
        m=re.match(r'^\s*Núm\.\s*(\d+)\.\s+(.*\S)\s*$',ln)
        if m:
            t=m.group(2)
            if isup(t):
                cur={'pr':prov,'n':int(m.group(1)),'tit':t,'c':[],'s':[]}; out.append(cur); sup=False; pend=True; continue
            if cur is None: continue
            pend=False; (cur['s'] if sup else cur['c']).append((int(m.group(1)),t.rstrip('.'))); continue
        if re.match(r'^\s*Núm\.\s*$',ln): continue
        if re.match(r'^\s*Suplentes:?\s*$',ln): sup=True; pend=False; continue
        if cur and pend and isup(ln.strip()): cur['tit']+=' '+ln.strip(); continue
        if cur and not pend and (cur['s'] if sup else cur['c']) and re.match(r'^\s+[A-ZÁÉÍÓÚa-záéíóúñ]',ln) and len(ln.strip())<40 and not isup(ln.strip()) and re.search(r'[a-z]',ln):
            print('CONT?',prov,repr(ln.strip())[:80],file=sys.stderr)
        else: print('??',prov,repr(ln[:110]),file=sys.stderr)
    return out
if __name__=='__main__':
    C=parse(sys.argv[1]); print(len(C),sum(len(c['c'])+len(c['s']) for c in C))
    for c in C:
        o=[x[0] for x in c['c']]; so=[x[0] for x in c['s']]
        if o!=list(range(1,len(o)+1)) or so!=list(range(1,len(so)+1)): print('  ORD',c['pr'],c['tit'],o,so)
    print(collections.Counter(c['pr'] for c in C)); print(sorted({re.sub(r'\s+',' ',c['tit']) for c in C}))
