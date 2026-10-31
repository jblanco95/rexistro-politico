import re,sys,unicodedata,collections
from res import *
from pc import parse
sys.path.insert(0,'/home/user/work/and')
from parse_cand import splitname
def toks(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return tuple(sorted(w for w in re.sub(r'[^a-zñ ]',' ',s).split() if w not in ('de','del','la','las','los','y','i','m','ª')))
PARTY=re.compile(r'(Partido Popular|Partido Socialista Obrero Español de Andalucía|Izquierda Unida.*|Podemos|Ciudadanos.*)$')
PK={'Partido Popular':'PP','Partido Socialista Obrero Español de Andalucía':'PSOE-A','Podemos':'PODEMOS'}
def pk(s): return PK.get(s) or ('IULV-CA' if s.startswith('Izquierda') else 'CS')
def electos(y):
    L=open(D0+FILES[y][1],encoding='utf8').read().replace('\t','   ').split('\n')
    i=[k for k,l in enumerate(L) if 'PROCLAMADOS ELECTOS' in l.upper()][-1]
    out=collections.defaultdict(list); cur=None
    for l in L[i+1:]:
        s=l.strip()
        if s.upper() in PN and s==s.upper(): cur=PN[s.upper()]; continue
        m=re.match(r'^(\d+)\s+(.*\S)$',s)
        if m and cur:
            rest=m.group(2); pm=PARTY.search(rest)
            if not pm: print('?',s,file=sys.stderr); continue
            nm=' '.join(x.strip() for x in re.split(r'\s{2,}',rest[:pm.start()].strip()) if x.strip())
            parts=[x.strip() for x in re.split(r'\s{2,}',rest[:pm.start()].strip()) if x.strip()]
            disp=(parts[1]+' '+parts[0]) if (y=='2012' and len(parts)==2) else ' '.join(parts)
            out[cur].append((disp,pk(pm.group(1))))
    return out
if __name__=='__main__':
    for y in FILES:
        E=electos(y); tot,V,S=results(y); C=[c for c in parse(D0+FILES[y][0]) if not c.get('np')]
        for P in PROV:
            pv=PN[P]; assert len(E[pv])==SEATS[pv],(y,pv,len(E[pv]))
            for c in C:
                if c['pr']!=pv: continue
                g=key_of(c['tit']); n=S.get((P,g),0)
                el=[(n2,g2) for n2,g2 in E[pv] if g2==g]
                if len(el)!=n: print('SEATCOUNT',y,pv,g,len(el),n)
                tit={toks(splitname(r)[0]):o for o,r in c['c']}
                for n2,_ in el:
                    o=tit.get(toks(n2))
                    if o is None: print('NOMATCH',y,pv,g,n2)
                    elif o>n: print('LATE',y,pv,g,n2,o,n)
