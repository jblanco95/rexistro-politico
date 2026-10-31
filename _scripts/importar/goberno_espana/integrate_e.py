import json,re,collections,sys,os,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from parse import norm
from pair import sim
CONNW={'de','del','la','las','los','y','i'}
norm2=lambda s:' '.join(w for w in norm(s).split() if w not in CONNW)
SRC,DST=sys.argv[1],sys.argv[2]
CUT='2018-06-08'
D=json.load(open(f'{SRC}/data.json'))
PARTS={f:json.load(open(f'{SRC}/{f}')) for f in D['parts']}
pl=lambda x:x['p'] if isinstance(x,dict) else x
ALL=list(D['p'])+[p for f in D['parts'] for p in pl(PARTS[f])]
BYN=collections.defaultdict(list)
for p in ALL:
    for nm in {norm(p['n'])}|{norm(a) for a in p.get('alt',[])}: BYN[nm].append(p)
R=json.load(open('recs.json'))
# rexistros E existentes que non son cargos (delegacións para actos)
DEL=re.compile(r'que asistir|asistirá|ceremonia|beatificaci|Consistorio',re.I)
for p in ALL:
    if any(r['t']=='E' and DEL.search(r.get('c','')) for r in p['r']): p['r']=[r for r in p['r'] if not (r['t']=='E' and DEL.search(r.get('c','')))]
for f in D['parts']:
    x=PARTS[f]; L=pl(x); L[:]=[p for p in L if p['r']]
D['p']=[p for p in D['p'] if p['r']]
ALL=[p for p in ALL if p['r']]
st=collections.Counter()
# ---- validación contra os rexistros E existentes (xuño 2018 →)
EX=[(p,r) for p in ALL for r in p['r'] if r['t']=='E']
mine=collections.defaultdict(list)
for r in R: mine[norm2(r['n'])].append(r)
hit=0; miss=[]
for p,r in EX:
    if not r.get('i') or r['i']<CUT: continue
    L=[x for x in mine.get(norm2(p['n']),[]) if x.get('i')==r['i']] or [x for x in mine.get(norm2(p['n']),[]) if x.get('dn')==r.get('dn')]
    if L: hit+=1
    else: miss.append((p['n'],r['c'],r['i'],r.get('dn')))
newer=[r for r in R if (r.get('i') or '')>=CUT]
exk={(norm(p['n']),r.get('i')) for p,r in EX}|{(norm(p['n']),r.get('dn')) for p,r in EX}
extra=[r for r in newer if (norm(r['n']),r.get('i')) not in exk and (norm(r['n']),r.get('dn')) not in exk]
print(f'validación 2018+: existentes {sum(1 for p,r in EX if r.get("i") and r["i"]>=CUT)}, atopados {hit}; dos meus non presentes no existente: {len(extra)}')
json.dump({'miss':miss,'extra':[(r['n'],r['c'],r.get('i'),r.get('dn')) for r in extra]},open('validacion.json','w'),ensure_ascii=False,indent=0)
# ---- rexistros a engadir: os que comezan antes do corte (ou sen data de inicio e remate antes do corte)
import datetime
def dd(a,b): return abs((datetime.date.fromisoformat(a)-datetime.date.fromisoformat(b)).days)
EXN=collections.defaultdict(list)
for p,r in EX: EXN[norm2(p['n'])].append(r)
def dup(r):
    for x in EXN.get(norm2(r['n']),[]):
        if r.get('dn') and x.get('dn')==r['dn']: return True
        if sim(x['c'],r['c'])>=0.6 and x.get('i') and r.get('i') and dd(x['i'],r['i'])<45: return True
        if sim(x['c'],r['c'])>=0.6 and not x.get('i') and r.get('f') and x.get('f')==r.get('f'): return True
    return False
add=[r for r in R if (r.get('i') or r.get('f') or '')<CUT]
ext=[r for r in R if (r.get('i') or r.get('f') or '')>=CUT and not dup(r)]
print('engádense de 2018+ (non estaban):',len(ext))
add+=ext
SUPRA=set('GNUCEKXQSD')
nextid=max(int(p['id']) for p in ALL)+1; NEWP=[]
def mk(r):
    o={'t':'E','lx':r['lx'],'c':r['c'],'nv':r['nv'],'dp':r['dp']}
    for k in ('i','f','dn','un','dc','uc','oi','nt'):
        if r.get(k): o[k]=r[k]
    return o
for r in sorted(add,key=lambda r:r.get('i') or r.get('f')):
    k=norm(r['n']); rec=mk(r)
    # completar un rexistro existente sen data de inicio (nomeamento anterior a xuño 2018)
    done=False
    for p in BYN.get(k,[]):
        for x in p['r']:
            if x['t']=='E' and not x.get('i') and x.get('oi') and sim(x['c'],r['c'])>=0.5 and (not r.get('f') or r['f']>=CUT):
                x['i']=r['i']; x['dn']=r.get('dn'); x['un']=r.get('un'); x.pop('oi',None); x['lx']=r['lx'] if '–' in r['lx'] else x['lx']
                done=True; st['completa_existente']+=1; break
        if done: break
    if done: continue
    if r.get('f') and r['f']>=CUT and any(x['t']=='E' and sim(x['c'],r['c'])>=0.6 and (not x.get('i') or (r.get('i') and dd(x['i'],r['i'])<45) or x.get('f')==r.get('f')) for p in BYN.get(k,[]) for x in p['r']): st['xa_no_existente']+=1; continue
    cand=BYN.get(k,[])
    pick=None
    if cand:
        sup=[p for p in cand if any(x['t'] in SUPRA for x in p['r'])]
        if len(sup)>=1:
            pick=sorted(sup,key=lambda p:(-sum(1 for x in p['r'] if x['t']=='E'),-sum(1 for x in p['r'] if x['t'] in 'GNQ'),-len(p['r'])))[0]
        elif len(cand)==1 and len(k.split())>=4:
            pick=cand[0]
    if pick:
        pick['r'].append(rec); st['persoa_existente']+=1
        if r['n']!=pick['n'] and r['n'] not in pick.get('alt',[]) : pass
        continue
    p={'id':str(nextid),'n':r['n'],'s':r['s'],'r':[rec]}; nextid+=1
    NEWP.append(p); BYN[k].append(p); st['persoa_nova']+=1
print(st, 'novas persoas',len(NEWP))
os.makedirs(DST,exist_ok=True)
pl(PARTS[D['parts'][-1]]).extend(NEWP)
D['meta']['fontes'].insert(0,'Goberno de España 1977–2018: nomeamentos e ceses de altos cargos (Presidencia, vicepresidencias, ministerios, secretarías de estado, subsecretarías, secretarías xerais e xerais técnicas, direccións xerais, delegacións do Goberno, gobernos civís e principais organismos) nos reais decretos da sección II.A do BOE, rastrexados nos sumarios diarios da API de datos abertos do BOE entre o 01/01/1977 e o 31/10/2026; os decretos colectivos lense do texto ou do PDF orixinal')
D['meta']['actualizado']='2026-10-31'
json.dump(D,open(f'{DST}/data.json','w'),ensure_ascii=False,separators=(',',':'))
for f,x in PARTS.items(): json.dump(x,open(f'{DST}/{f}','w'),ensure_ascii=False,separators=(',',':'))
shutil.copy(f'{SRC}/index.html',f'{DST}/index.html')
