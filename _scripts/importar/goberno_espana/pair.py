import json,re,collections,sys
from parse import norm
STOP={'de','del','la','las','los','el','y','en','para','a','e','con','sin','por'}
def stems(c):
    w=[x for x in norm(c).split() if x not in STOP]
    return set(x[:6] for x in w)
def sim(a,b):
    A,B=stems(a),stems(b)
    return len(A&B)/max(1,len(A|B))
def pkey(n): return norm(n)
def pair(ev):
    ev=sorted(ev,key=lambda e:(e['d'],0 if e['k']=='c' else 1))  # ceses antes que nomeamentos no mesmo día
    open_=collections.defaultdict(list); recs=[]
    for e in ev:
        k=pkey(e['n'])
        if e['k']=='n':
            # duplicado (mesmo nomeamento publicado dúas veces / corrección)
            if any(o['dn']==e['dn'] for o in open_[k]): continue
            r={'n':e['n'],'s':e['s'],'c':e['c'],'nv':e['nv'],'dp':e['dep'],'i':e['d'],'dn':e['dn'],'un':e['u']}
            open_[k].append(r); recs.append(r)
        else:
            cands=[(sim(o['c'],e['c'])+(0.2 if o['nv']==e['nv'] else 0),o) for o in open_[k]]
            cands=[x for x in cands if x[0]>=0.45]
            if cands:
                o=max(cands,key=lambda x:(x[0],x[1]['i']))[1]
                o['f']=e['d']; o['dc']=e['dn']; o['uc']=e['u']; open_[k].remove(o)
            else:
                recs.append({'n':e['n'],'s':e['s'],'c':e['c'],'nv':e['nv'],'dp':e['dep'],'f':e['d'],'dc':e['dn'],'uc':e['u'],'oi':'nomeamento non atopado'})
    return recs
if __name__=='__main__':
    ev=json.load(open('events.json'))
    R=pair(ev)
    c=collections.Counter(('i' in r,'f' in r) for r in R); print(len(R),c)
    for r in R:
        if r['nv'] in('Ministro/a','Presidencia','Vicepresidencia','Secretaría de Estado'): print(r.get('i'),r.get('f'),r['n'],'|',r['c'])
