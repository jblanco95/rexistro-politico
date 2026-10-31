import json,re,sys,collections,unicodedata,os,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,'/home/user/work/and')
from build_and import *
from electos import electos_names,norm
SRC,DST=sys.argv[1],sys.argv[2]
DATES={'2004':'2004-03-14','2008':'2008-03-09'}
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
NAMEFIX={('2004','Manuel Chaves González'):'Manuel María Chaves González'}
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
# ---- build new candidacies (2004, 2008)
sys.path.insert(0,'/home/user/work/and3')
from res0408 import results as res3, key_of, ca_of, FILES as F3, PN as PN3, SGOUT, PROV as PROV3, SEATS as SEATS3, D0 as D03
from pc import parse as p08
from pc04 import parse as p04
from el0408 import electos as el3, toks
FS=json.load(open('/home/user/work/and3/firstsex.json'))
# Corrección de erros das candidaturas de 2008 (BOJA núm. 37, 21/02/2008): (prov, lista, tipo, posto) -> nome correcto
CORR08={('Almería','IULV-CA','Titular',4):'Don Rodrigo José Rodríguez Soler',('Cádiz','CANDA','Titular',1):'Don José Ortega Andrade',
 ('Cádiz','CA','Titular',8):'Doña Sara María Rodríguez Martín',('Cádiz','UPYD','Titular',5):'Don Hugo Cañellas Ávila',
 ('Córdoba','SAIN','Titular',1):'Doña María Esther Moleón Paiz',('Córdoba','VERDES','Titular',3):'Don Jonatan Frutos Frutos',
 ('Córdoba','VERDES','Titular',12):'Doña Rosa María Ruiz Escobar',('Córdoba','FE DE LAS JONS','Titular',4):'Doña Gracia Collado Montanero',
 ('Granada','CANDA','Suplente',1):'Doña María Isabel Garrido Asenjo',('Granada','CANDA','Suplente',2):'Don Antonio Moya Martín',
 ('Granada','CANDA','Suplente',3):'Doña Montserrat Martín Escobar',('Granada','CANDA','Suplente',4):'Don Rafael Contreras Fernández',
 ('Jaén','PCPA','Titular',12):'Doña María Luisa Ávila de la Casa',('Jaén','IR','Titular',11):'Doña Carmen Brun Esquileche',
 ('Málaga','PSOE-A','Suplente',1):'Doña María Josefa Anés Íñiguez',('Málaga','UPYD','Titular',7):'Doña Rosa Gemma Flores Rodríguez',
 ('Málaga','PCPA','Titular',11):'Don Juan de Sosa Montesinos'}
CANAME08={('Almería','PSOE-A'):'PARTIDO SOCIALISTA OBRERO ESPAÑOL DE ANDALUCÍA',('Granada','IULV-CA'):'IZQUIERDA UNIDA LOS VERDES-CONVOCATORIA POR ANDALUCÍA'}
NEW=[]; AR={}; usedc=collections.Counter()
def fsx(n):
    w=unicodedata.normalize('NFD',n.split()[0].lower()); w=''.join(ch for ch in w if unicodedata.category(ch)!='Mn'); return FS.get(w)
for y in ['2004','2008']:
    tot,V,S=res3(y); SE=SEATS3[y]
    C=[c for c in (p04 if y=='2004' else p08)(D03+F3[y][0]) if not c.get('np')]
    # sexo dos electos de 2004 (o BOJA de electos usa Don/Doña)
    ESX={}
    if y=='2004':
        T=open(D03+F3[y][1],encoding='utf8').read()
        for m in re.finditer(r'(Don|Doña)\s+([^\n]+?)\.?(?:\s{2,}|\n)',T): ESX[toks(m.group(2))]='M' if m.group(1)=='Doña' else 'H'
    for c in C:
        pv=c['pr']; P=[k for k,v in PN3.items() if v==pv][0]; g=key_of(c['tit']); sg=SGOUT.get(g,g); ca=CANAME08.get((pv,g)) if y=='2008' else None; ca=ca or ca_of(c['tit'])
        es=S.get((P,g),0); vt=V.get((P,g))
        for tp,L in (('Titular',c['c']),('Suplente',c['s'])):
            for o,raw in L:
                if y=='2008' and (pv,g,tp,o) in CORR08: raw=CORR08[(pv,g,tp,o)]; usedc[(pv,g,tp,o)]+=1
                n,sx,ind,pi,al=clean(raw)
                si=False
                if n.isupper(): n=tcase(n)
                n=re.sub(r'\s*-\s*','-',n); orig=n; n=NAMEFIX.get((y,n),n)
                if sx is None:
                    sx=ESX.get(toks(n)) or fsx(n)
                    if sx is None: sx='M'
                    si=toks(n) not in ESX
                rec=dict(orig=orig,y=y,pr=pv,sg=sg,ca=ca,tp=tp,o=o,n=n,sx=sx,si=si,ind=ind,pi=pi,al=al,vt=vt,es=es)
                if tp=='Titular':
                    el=o<=es; rec['el']=el
                    rec['po']='Electo/a' if el else ('Primeiro/a non electo/a' if es and o==es+1 else 'Non electo')
                else: rec['el']=False; rec['po']='Suplente'
                NEW.append(rec)
    for pv in AND: assert sum(1 for r in NEW if r['y']==y and r['pr']==pv and r['el'])==SE[pv]
    full={}
    for c in C: full.setdefault((c['pr'],key_of(c['tit'])),(CANAME08.get((c['pr'],key_of(c['tit']))) if y=='2008' else None) or ca_of(c['tit']))
    gs=sorted({k[1] for k in V})
    for P in PROV3+['TOTAL']:
        pv=PN3.get(P,'Andalucía'); t=tot[P]; rows=[]
        for g in gs:
            v=V[(P,g)]
            if not v: continue
            nm=collections.Counter(full[(q,g)] for q in AND if (q,g) in full).most_common(1)[0][0] if pv=='Andalucía' else full[(pv,g)]
            rows.append([nm,SGOUT.get(g,g),v,round(100*v/t[2],2),S[(P,g)]])
        rows.sort(key=lambda x:(-x[2],x[1]))
        AR[f'{y}|{pv}']={'t':[t[0],t[1],t[2],t[4],t[5],109 if pv=='Andalucía' else SE[pv]],'l':rows}
assert len(usedc)==len(CORR08), set(CORR08)-set(usedc)
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
json.dump({'amb':amb,'home':HOME},open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'match_report3.json'),'w'),ensure_ascii=False,indent=0)
# ---- write
os.makedirs(DST,exist_ok=True)
last=D['parts'][-1]; x=PARTS[last]; plist(x).extend(NEWP)
D['ar'].update(AR)
k=[i for i,f in enumerate(D['meta']['fontes']) if f.startswith('Parlamento de Andalucía 2012')][0]
D['meta']['fontes'].insert(k,'Parlamento de Andalucía 2004 e 2008: candidaturas proclamadas (BOJA núm. 32, 17/02/2004, e BOJA núm. 30, 12/02/2008, coa corrección de erros do BOJA núm. 37, 21/02/2008, Xunta Electoral de Andalucía); resultados e electos: BOJA núm. 62, 30/03/2004 (Resolución do 26/03/2004) e BOJA núm. 63, 01/04/2008 (Resolución do 26/03/2008)')
json.dump(D,open(f'{DST}/data.json','w'),ensure_ascii=False,separators=(',',':'))
for f,x in PARTS.items(): json.dump(x,open(f'{DST}/{f}','w'),ensure_ascii=False,separators=(',',':'))
json.dump(NEW,open('/home/user/work/and3/new_recs.json','w'),ensure_ascii=False,indent=0)
print('new persons',len(NEWP),'records',len(NEW))
