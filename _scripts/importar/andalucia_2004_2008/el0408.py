import re,sys,unicodedata,collections
from res0408 import *
from pc import parse as p08
from pc04 import parse as p04
sys.path.insert(0,'/home/user/work/and')
from parse_cand import splitname
def toks(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return frozenset(w for w in re.sub(r'[^a-zñ ]',' ',s).split() if w not in ('de','del','la','las','los','y','i','don','dona'))
def electos(y):
    T=open(D0+FILES[y][1],encoding='utf8').read()
    T=T[T.upper().rfind('RELACI'):] if y=='2008' else T[T.find('Relación de diputados'):]
    out=[]
    for l in T.split('\n'):
        for part in re.split(r'\s{2,}',l):
            m=re.match(r'^(Don|Doña)\s+(.+?)\.?$',part.strip())
            if m: out.append(m.group(2))
    return out
def check(y,C):
    E=electos(y); ET=[toks(n) for n in E]; tot,V,S=results(y); exp=[]
    for c in C:
        P=[k for k,v in PN.items() if v==c['pr']][0]; n=S.get((P,key_of(c['tit'])),0)
        exp+=[(c['pr'],key_of(c['tit']),o,splitname(r)[0]) for o,r in c['c'][:n]]
    print(y,'electos no BOJA',len(E),'esperados',len(exp))
    used=set()
    for pv,g,o,n in exp:
        t=toks(n); hit=[i for i,e in enumerate(ET) if e==t] or [i for i,e in enumerate(ET) if len(e&t)>=max(2,len(t)-1) and i not in used]
        if not hit: print('  sen casar',pv,g,o,n)
        else: used.add(hit[0])
    for i,e in enumerate(E):
        if i not in used: print('  electo non esperado',e)
if __name__=='__main__':
    check('2004',p04(D0+FILES['2004'][0])); check('2008',p08(D0+FILES['2008'][0]))
