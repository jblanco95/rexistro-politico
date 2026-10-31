import re,unicodedata
from build_and import *
def norm(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=re.sub(r'[^a-z ]',' ',s); return ' '.join(s.split())
def electos_names(y):
    L=open(FILES[y][1],encoding='utf8').read().split('\n')
    i=[k for k,l in enumerate(L) if re.search(r'(?i)proclamados electos',l)][-1]
    out={}; cur=None; last=None
    PARTY=r'(Partido Popular|PSOE-A|Partido Socialista Obrero Español de Andalucía|Vox|Ciudadanos|Adelante Andalucía.*|Izquierda Unida Andalucía.*)$'
    for l in L[i+1:]:
        s=l.strip()
        if not s: continue
        up=s.upper()
        if up in PROV: cur=PN[up]; out[cur]=[]; continue
        if cur is None: continue
        m=re.match(r'^(?:\d+\s+)?(.+?)\s{2,}'+PARTY,s)
        if m: out[cur].append([m.group(1),m.group(2)]); last=out[cur][-1]; continue
        if re.match(r'^(de |del |la )',s) and last and len(s)<40 and '  ' not in s: last[0]+=' '+s
    return out
if __name__=='__main__':
    for y in ['2018','2022']:
        E=electos_names(y); tot,V,S=results(y)
        C=[c for c in parse(FILES[y][0]) if not c.get('np')]
        for pv in E:
            P=[k for k,v in PN.items() if v==pv][0]
            exp=[]
            for c in C:
                if c['pr']!=pv: continue
                g=sg_of(y,c['tit']); n=S.get((P,g),0)
                exp+= [(splitname(r)[0],g) for o,r in c['c'][:n]]
            En=[norm(n) for n,_ in E[pv]]; Xn=[norm(n) for n,_ in exp]
            print(y,pv,len(En),len(Xn))
            for n in Xn:
                if n not in En: print('   expected not in electos:',n)
            for n in En:
                if n not in Xn: print('   electos not expected:',n)
