import re,sys
sys.path.insert(0,'/home/user/work/and')
from parse_cand import splitname,PROVS
NOISE=re.compile(r'BOJA núm|Boletín Oficial de la Junta|^\s*\d{8}\s*$|^\s*Página núm|Depósito Legal')
def parse(path):
    L=open(path,encoding='utf8').read().replace('\t',' ').split('\n')
    out=[];prov=None;cur=None;sup=False;pend=False;started=False
    for ln in L:
        if NOISE.search(ln): continue
        if not ln.strip(): pend=False; continue
        m=re.search(r'Circunscripción [Ee]lectoral:\s*(\S.*\S)',ln)
        if m: prov=m.group(1).strip(); assert prov in PROVS,prov; cur=None; continue
        if prov is None: continue
        m=re.match(r'^\s*(?:Candidatura núm\.:\s*)?(\d+)\.\s+(?!Don\b|Doña\b|D\.\s|Dª)(\S.*\S)\s*$',ln)
        if m and not re.match(r'(?i)(don|doña)\b',m.group(2)):
            cur={'pr':prov,'n':int(m.group(1)),'tit':m.group(2),'c':[],'s':[]}; out.append(cur); sup=False; pend=True; continue
        if cur is None: continue
        if 'NO PROCLAMADA' in ln: cur['np']=True; continue
        if re.match(r'^\s*Suplentes:?\s*$',ln): sup=True; pend=False; continue
        m=re.match(r'^\s*(\d+)\.\s+(.*\S)\s*$',ln)
        if m: pend=False; (cur['s'] if sup else cur['c']).append((int(m.group(1)),re.sub(r'^(Don|Doña)\.\s',r'\1 ',m.group(2)))); continue
        if pend and ln.strip().upper()==ln.strip(): cur['tit']+=' '+ln.strip(); continue
        if (cur['s'] if sup else cur['c']) and re.match(r'^\s{0,20}[a-záéíóúñ]',ln) :
            L2=(cur['s'] if sup else cur['c']); L2[-1]=(L2[-1][0],L2[-1][1]+' '+ln.strip()); continue
        print('??',prov,repr(ln[:120]),file=sys.stderr)
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        C=parse(f); print(f,len(C),sum(len(c['c'])+len(c['s']) for c in C))
        import collections
        for c in C:
            o=[x[0] for x in c['c']]; so=[x[0] for x in c['s']]
            if o!=list(range(1,len(o)+1)) or so!=list(range(1,len(so)+1)): print('  ORD',c['pr'],c['tit'],o,so)
            for _,r in c['c']+c['s']:
                if splitname(r)[1] is None: print('  NAME',c['pr'],c['tit'][:30],repr(r))
        print(collections.Counter(c['pr'] for c in C))
        print(sorted({re.sub(r'\s+',' ',c['tit']) for c in C}))
