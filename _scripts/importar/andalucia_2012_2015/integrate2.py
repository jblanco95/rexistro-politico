import json,re,sys,collections,unicodedata,os,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,'/home/user/work/and')
from build_and import *
from electos import electos_names,norm
SRC,DST=sys.argv[1],sys.argv[2]
DATES={'2012':'2012-03-25','2015':'2015-03-22'}
AND=['Almería','Cádiz','Córdoba','Granada','Huelva','Jaén','Málaga','Sevilla']
ANDC=('04','11','14','18','21','23','29','41')
FIX0={('2018','Sevilla','PSOE-A',6):'José Sánchez Muñoz', ('2022','Cádiz','PSOE-A',3):None}
RENUN={('2018','Cádiz','PP','José Ortiz Galván'),('2018','Sevilla','PP','Juan Ignacio Zoido Álvarez')}
ELX={('2022','Cádiz','Rocío Arrabal Higuera')}  # no BOJA de electos figura como «Higueras»
# mesma persoa con nome escrito de xeito distinto en 2018 e 2022 (mesma lista ou partido afín)
NAMEFIX0={('2018','María Carmen Martínez García'):'María del Carmen Martínez García',
 ('2022','María Carmen Rodríguez Nieto'):'María del Carmen Rodríguez Nieto',
 ('2018','María Ángeles Sánchez Jiménez'):'María Ángeles Sánchez Jiménez',('2022','Mari Ángeles Sánchez Jiménez'):'María Ángeles Sánchez Jiménez',
 ('2018','Rodrigo Alonso Fernández'):'Rodrigo Javier Alonso Fernández',
 ('2022','Rosario Carvajal Ávila'):'María Rosario Carvajal Ávila',
 ('2022','Rocío Caridad Díaz Marín'):'Rocío de la Caridad Díaz Marín',
 ('2018','Ana Muñoz Colera'):'Ana María Muñoz Colera',
 ('2022','Aúgustin Marie Ndour Ndong'):'Agustín Marie Ndour Ndong',
 ('2022','Pilar Lucio Sarria'):'María Pilar Lucio Sarria',
 ('2022','Vicente de los Ríos Peñuela'):'Antonio Vicente de los Ríos Peñuela',('2018','Antonio Vicente De los Ríos Peñuela'):'Antonio Vicente de los Ríos Peñuela',
 ('2022','Salvador Benítez Rodríguez'):'Salvador Lorenzo Benítez Rodríguez',
 ('2022','Ana Sánchez Torres'):'Ana Isabel Sánchez Torres',
 ('2022','Ana Muñoz Galán'):'Ana María Muñoz Galán',
 ('2018','Natividad Ángela Pérez Cáceres'):'Natividad Ángeles Pérez Cáceres',
 ('2018','Teresa Rodríguez-Rubio Vázquez'):'María Teresa Rodríguez-Rubio Vázquez',
 ('2018','José María Benito Saucedo'):'José María de Benito Saucedo'}
NAMEFIX={}
LOW={'de','del','la','las','los','y','e','i','da','do','dos','das','en'}
def tcase(s):
    out=[]
    for w in s.split(' '):
        lw=w.lower()
        if lw in LOW and out: out.append(lw); continue
        w=re.sub(r"(^|[-´'’.])(\w)",lambda m:m.group(1)+m.group(2).upper(),lw)
        w=w.replace('Mª','Mª').replace('M.ª','M.ª')
        out.append(w)
    return ' '.join(out)
def clean(raw):
    n,sx,ind,pi=splitname(raw)
    al=None
    m=re.search(r'\s*\(([^()]+)\)\s*',n)
    if m: al=m.group(1).strip(); n=(n[:m.start()]+' '+n[m.end():]).strip()
    m=re.search(r'\s*["«“]([^"»”]+)["»”]\s*',n)
    if m: al=m.group(1).strip(); n=(n[:m.start()]+' '+n[m.end():]).strip()
    n=' '.join(n.split()); n=re.sub(r'\s*-\s*','-',n)
    return n,sx,ind,pi,al
# ---- load
D=json.load(open(f'{SRC}/data.json'))
PARTS={f:json.load(open(f'{SRC}/{f}')) for f in D['parts']}
def plist(x): return x['p'] if isinstance(x,dict) else x
ALL=list(D['p'])+[p for f in D['parts'] for p in plist(PARTS[f])]
BYN=collections.defaultdict(list)
for p in ALL:
    for nm in {norm(p['n'])}|{norm(a) for a in p.get('alt',[])}: BYN[nm].append(p)
def andlink(p):
    for r in p['r']:
        if r.get('pr') in AND or str(r.get('ine','')).startswith(ANDC) or r.get('cc')=='Andalucía' or r.get('ca')=='Andalucía' or 'Andaluc' in str(r.get('lu','')) or r.get('e')=='Parlamento de Andalucía': return True
    return False
# ---- build new candidacies (2012, 2015)
sys.path.insert(0,'/home/user/work/and2')
from res import results as res2, key_of, ca_of, FILES as F2, PN as PN2, SGOUT, PROV as PROV2
from pc import parse as parse2
NEW=[]; AR={}
def fixcase(n):
    w=n.split(' '); return ' '.join(x if i==0 or x not in ('De','Del','La','Las','Los','Y') else x.lower() for i,x in enumerate(w))
for y in ['2012','2015']:
    tot,V,S=res2(y)
    C=[c for c in parse2('/home/user/work/and2/'+F2[y][0]) if not c.get('np')]
    for c in C:
        pv=c['pr']; P=[k for k,v in PN2.items() if v==pv][0]; g=key_of(c['tit']); sg=SGOUT.get(g,g); ca=ca_of(c['tit'])
        es=S.get((P,g),0); vt=V.get((P,g))
        for tp,L in (('Titular',c['c']),('Suplente',c['s'])):
            for o,raw in L:
                n,sx,ind,pi,al=clean(raw)
                si=False
                if sx is None: sx='M'; si=True
                if n.isupper(): n=tcase(n)
                n=fixcase(re.sub(r'\s*-\s*','-',n)); orig=n; n=NAMEFIX.get((y,n),n)
                rec=dict(orig=orig,y=y,pr=pv,sg=sg,ca=ca,tp=tp,o=o,n=n,sx=sx,si=si,ind=ind,pi=pi,al=al,vt=vt,es=es)
                if tp=='Titular':
                    el=o<=es; rec['el']=el
                    rec['po']='Electo/a' if el else ('Primeiro/a non electo/a' if es and o==es+1 else 'Non electo')
                else: rec['el']=False; rec['po']='Suplente'
                NEW.append(rec)
    for pv in AND: assert sum(1 for r in NEW if r['y']==y and r['pr']==pv and r['el'])==SEATS[pv]
    full={}
    for c in C: full.setdefault((c['pr'],key_of(c['tit'])),ca_of(c['tit']))
    gs=sorted({k[1] for k in V})
    for P in PROV2+['TOTAL']:
        pv=PN2.get(P,'Andalucía'); t=tot[P]
        if y=='2015' and P=='SEVILLA': t=[1529823,1006136,995213,981500,13713,10923]
        if y=='2015' and P=='TOTAL': t=[6462627,4042961,4001812,3947095,54717,41149]
        rows=[]
        for g in gs:
            v=V[(P,g)]
            if not v: continue
            nm=collections.Counter(full[(q,g)] for q in AND if (q,g) in full).most_common(1)[0][0] if pv=='Andalucía' else full[(pv,g)]
            rows.append([nm,SGOUT.get(g,g),v,round(100*v/t[2],2),S[(P,g)]])
        rows.sort(key=lambda x:(-x[2],x[1]))
        AR[f'{y}|{pv}']={'t':[t[0],t[1],t[2],t[4],t[5],sum(SEATS.values()) if pv=='Andalucía' else SEATS[pv]],'l':rows}
# ---- match persons
nextid=max(int(p['id']) for p in ALL)+1; FIRSTNEW=nextid
SUP=[]; HOME=[]; NEWP=[]; stats=collections.Counter(); amb=[]
local={}  # norm name -> list of new persons created (for 2018/2022 linking)
def addalt(p,o):
    if o!=p['n'] and o not in p.get('alt',[]) and norm(o)!=norm(p['n']) : p.setdefault('alt',[]).append(o)
def mkrec(r):
    o={'t':'C','e':'Parlamento de Andalucía','d':DATES[r['y']],'pr':r['pr'],'sg':r['sg'],'ca':r['ca'],'tp':r['tp'],'o':r['o'],'el':r['el'],'po':r['po']}
    if r['vt'] is not None: o['vt']=str(r['vt']); o['es']=str(r['es'])
    if r['ind']: o['ind']=True
    if r['pi']: o['pi']=r['pi']
    if r['al']: o['al']=r['al']
    return o
for r in sorted(NEW,key=lambda r:(r['y'],AND.index(r['pr']))):
    k=norm(r['n']); rec=mkrec(r)
    cand=[p for p in BYN.get(k,[]) if andlink(p)]
    # same election already used? (one person can't be in two lists)
    cand=[p for p in cand if not any(x['t']=='C' and x['d']==rec['d'] for x in p['r'])]
    if len(cand)>1:
        pk=lambda s:re.sub(r'[^A-Z]','',unicodedata.normalize('NFD',str(s or '').upper()))[:4]
        def score(p):
            return (any(x['t']=='C' and x.get('e')=='Parlamento de Andalucía' for x in p['r']),
                    any(x.get('pr')==r['pr'] for x in p['r']),
                    any(pk(x.get('sg') or x.get('pa'))==pk(r['sg']) for x in p['r']),
                    len(p['r']), max(str(x.get('d') or x.get('y') or x.get('i') or '') for x in p['r']))
        cand=sorted(cand,key=score,reverse=True)
        amb.append((r['n'],r['y'],r['pr'],[p['id'] for p in cand])); stats['amb']+=1
        cand=cand[:1]
    if cand:
        p=cand[0]; p['r'].append(rec); stats['exist']+=1; addalt(p,r['orig'])
        if r['si'] and 's' not in p: p['s']=r['sx']
        continue
    BYN_all=[p for p in BYN.get(k,[]) if not p['id'].startswith('N')]
    pk4=lambda s:re.sub(r'[^A-Z]','',unicodedata.normalize('NFD',str(s or '').upper()))[:4]
    olds=[p for p in BYN_all if int(p['id'])<FIRSTNEW]
    if len(olds)==1 and not any(x['t']=='C' and x['d']==rec['d'] for x in olds[0]['r']) and any(x['t'] in 'UGNC' and pk4(x.get('sg'))==pk4(r['sg']) for x in olds[0]['r']):
        olds[0]['r'].append(rec); addalt(olds[0],r['orig']); stats['supra_party']+=1; SUP.append((r['n'],r['sg'],olds[0]['id'])); continue
    if BYN_all: stats['homonym_elsewhere']+=1; HOME.append((r['n'],r['y'],r['pr'],r['sg'],[(p['id'],[(x['t'],x.get('pr') or x.get('ine') or x.get('cc') or x.get('lu'),x.get('sg') or x.get('pa') or x.get('c')) for x in p['r']][:4]) for p in BYN_all]))
    p={'id':str(nextid),'n':r['n'],'s':r['sx']}
    if r['si']: p['si']=True
    p['r']=[rec]; nextid+=1; addalt(p,r['orig'])
    NEWP.append(p); BYN[k].append(p); stats['new']+=1
print(stats)
json.dump({'amb':amb,'home':HOME},open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'match_report2.json'),'w'),ensure_ascii=False,indent=0)
# ---- write
os.makedirs(DST,exist_ok=True)
last=D['parts'][-1]; x=PARTS[last]; plist(x).extend(NEWP)
D['ar'].update(AR)
k=[i for i,f in enumerate(D['meta']['fontes']) if f.startswith('Parlamento de Andalucía 2018')][0]
D['meta']['fontes'].insert(k,'Parlamento de Andalucía 2012 e 2015: candidaturas proclamadas (BOJA núm. 40, 28/02/2012, e BOJA núm. 37, 24/02/2015, Xunta Electoral de Andalucía); resultados e electos: BOJA núm. 74, 17/04/2012 (Resolución do 12/04/2012) e BOJA núm. 71, 15/04/2015 (Resolución do 14/04/2015), coa corrección de erros do escrutinio de Sevilla (BOJA núm. 77, 23/04/2015)')
json.dump(D,open(f'{DST}/data.json','w'),ensure_ascii=False,separators=(',',':'))
for f,x in PARTS.items(): json.dump(x,open(f'{DST}/{f}','w'),ensure_ascii=False,separators=(',',':'))
json.dump(NEW,open('/home/user/work/and2/new_recs.json','w'),ensure_ascii=False,indent=0)
print('new persons',len(NEWP),'records',len(NEW))
