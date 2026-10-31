import json,re,collections,sys,os,concurrent.futures as cf
from parse import norm,rd_date,split_title
from extract import events,nvOf,depOf,MIL
from multi import doc_text,parse_body
from pair import sim
LEG=[('Constituínte','1977-07-13'),('I','1979-03-27'),('II','1982-11-18'),('III','1986-07-15'),('IV','1989-11-21'),('V','1993-06-29'),('VI','1996-03-27'),('VII','2000-04-05'),('VIII','2004-04-02'),('IX','2008-04-01'),('X','2011-12-13'),('XI','2016-01-13'),('XII','2016-07-19'),('XIII','2019-05-21'),('XIV','2019-12-03'),('XV','2023-08-17')]
def legAt(d):
    k=0
    for i,(n,c) in enumerate(LEG):
        if d>=c: k=i
    return k
def lxOf(i,f):
    a=legAt(i or f); b=legAt(f or '2026-10-31')
    return LEG[a][0] if a==b else LEG[a][0]+'–'+LEG[b][0] if b==a+1 else '–'.join(x[0] for x in LEG[a:b+1])
KW=re.compile(r'Ministr|Vicepresident|altos cargos|Secretari|Subsecretari|Director|Gobernador|Delegad|Presidente del Gobierno|Interventor|Fiscal General|Abogad',re.I)
NOKW=re.compile(r'provinciales|territoriales|Consejeros del Reino|Consejo de Regencia|Magistrad|Fiscales|Embajad|Agregad|Vocales|Consejeros|Jueces|Notari|Registrador|Profesor|Catedr|Académic|Rector|Capitanes|Generales|Almirant|Coronel',re.I)
def multi_events(multi):
    sel=[m for m in multi if KW.search(m[3]) and not NOKW.search(m[3])]
    print('multi seleccionados',len(sel),'de',len(multi),flush=True)
    def one(m):
        day,bid,dep,t=m
        try: tx=doc_text(bid) or ''
        except Exception as e: tx=''
        res=parse_body(tx,t)
        if not res and tx and re.search(r'Ministros|Vicepresidentes',t):
            try:
                import subprocess
                raw=subprocess.run(['pdftotext',f'docs/{bid}.pdf','-'],capture_output=True,text=True).stdout
                raw=re.sub(r'\u00ad\s*\n(?=[A-ZÁÉÍÓÚÑ])','-',raw).replace('\u00ad\n','').replace('\u00ad','')
                raw=re.sub(r'\s+',' ',raw)
                from parse import take_name
                res=[]
                for mm in re.finditer(r'((?:Ministr[oa]|Vicepresident[ea])[^,;:]{3,120}?),\s+a\s+(don|doña)\s+',raw):
                    nm=take_name(raw[mm.end():])
                    if nm and not re.search(r'cese',raw[max(0,mm.start()-60):mm.start()]): res.append((nm,'M' if mm.group(2)=='doña' else 'H',re.sub(r'\s+',' ',mm.group(1)).replace('Transportes. Turismo','Transportes, Turismo')))
            except Exception as e: print('fallo',bid,e)
        return m,res
    out=[]; nil=[]
    with cf.ThreadPoolExecutor(4) as ex:
        for m,res in ex.map(one,sel):
            day,bid,dep,t=m
            kind='c' if re.search(r'\bces',t,re.I) and not re.search(r'nombr',t,re.I) else 'n'
            dn,dd=rd_date(t); pub=f'{day[:4]}-{day[4:6]}-{day[6:]}'
            if not res: nil.append(m)
            for nm,sx,c in res:
                if ',' in nm: continue
                c=re.split(r',?\s+y por (?:el|la) que |\.\s+Se nombra|,?\s+y se dispone ',c)[0]
                c=re.sub(r'\s+',' ',c).replace(' la. ',' la ')
                c=re.sub(r'\s+(al|el) (Ministr|Secretari|Subsecretari).*$','',c); c=re.sub(r'\s+[aá]$','',c).strip(' ,.'); c=re.sub(r',\s*\w{0,2}$','',c).strip(' ,.')
                nv=nvOf(c,'')
                if not nv: continue
                out.append({'k':kind,'n':nm,'s':sx,'c':c,'nv':nv,'dep':depOf(dep),'d':dd or pub,'pub':pub,'dn':dn,'u':f'https://www.boe.es/diario_boe/txt.php?id={bid}','id':bid,'t':t,'multi':1})
    print('eventos de decretos colectivos',len(out),'sen resultado',len(nil),flush=True)
    json.dump(nil,open('multi_nil.json','w'),ensure_ascii=False,indent=0)
    return out
def cargoKey(r):
    return ' '.join(w[:6] for w in norm(re.sub(r',.*$','',r['c'])).split())
def build():
    ev,multi=events()
    print('eventos de títulos',len(ev),flush=True)
    ev+=multi_events(multi)
    json.dump(ev,open('events_all.json','w'),ensure_ascii=False)
    ev=sorted(ev,key=lambda e:(e['d'],0 if e['k']=='c' else 1))
    op=collections.defaultdict(list); recs=[]; seen=set()
    for e in ev:
        k=norm(e['n'])
        key=(k,e['dn'],e['k'],norm(e['c'])[:40])
        if key in seen: continue
        seen.add(key)
        if e['k']=='n':
            # renomeamento ao mesmo cargo sen cese (p. ex. novo goberno): pecha o anterior
            for o in list(op[k]):
                if sim(o['c'],e['c'])>=0.85 and o['nv']==e['nv']:
                    o['f']=e['d']; o['dc']='(renovado: '+(e['dn'] or 'novo nomeamento')+')'; op[k].remove(o)
            r={'n':e['n'],'s':e['s'],'c':e['c'],'nv':e['nv'],'dp':e['dep'],'i':e['d'],'dn':e['dn'],'un':e['u']}
            op[k].append(r); recs.append(r)
        else:
            cands=[(sim(o['c'],e['c'])+(0.2 if o['nv']==e['nv'] else 0),o) for o in op[k]]
            cands=[x for x in cands if x[0]>=0.45]
            if cands:
                o=max(cands,key=lambda x:(x[0],x[1]['i']))[1]
                o['f']=e['d']; o['dc']=e['dn']; o['uc']=e['u']; op[k].remove(o)
            else:
                recs.append({'n':e['n'],'s':e['s'],'c':e['c'],'nv':e['nv'],'dp':e['dep'],'f':e['d'],'dc':e['dn'],'uc':e['u'],'oi':'nomeamento anterior a 1977' if e['d']<'1978-01-01' else 'nomeamento non atopado no BOE'})
    # formación dun novo goberno: os ministros e vicepresidentes que seguen abertos e non son renomeados cesan ese día
    P0=sorted({r['i'] for r in recs if r['nv']=='Presidencia' and 'i' in r})
    mins=sorted([r for r in recs if r['nv'] in ('Ministro/a','Vicepresidencia') and 'i' in r],key=lambda r:r['i'])
    ngov=0
    for pd in P0:
        F=min([r['i'] for r in mins if r['i']>=pd and r['i']<=pd[:4]+'-12-31' or (r['i']>=pd and r['i']<str(int(pd[:4])+1)+'-01-31')] or [pd])
        newp={norm(r['n']) for r in mins if r['i']==F}
        for r in mins:
            if r['i']<pd and 'f' not in r:
                r['f']=F; r['nt']='Cesou coa formación do novo goberno ('+F+').' if norm(r['n']) not in newp else 'Renovado no novo goberno.'; r['fx']=1; ngov+=1
    print('pechados por novo goberno',ngov)
    # a mesma persoa nomeada despois para outro alto cargo a tempo completo
    FT={'Dirección xeral','Subsecretaría','Secretaría de Estado','Secretaría xeral','Secretaría xeral técnica','Ministro/a','Delegación do Goberno','Goberno civil','Vicepresidencia','Presidencia'}
    byp=collections.defaultdict(list)
    for r in recs:
        if 'i' in r: byp[norm(r['n'])].append(r)
    nmov=0
    for k,L in byp.items():
        L.sort(key=lambda r:r['i'])
        for a,b in zip(L,L[1:]):
            if 'f' not in a and a['nv'] in FT and b['nv'] in FT and b['i']>a['i'] and not (a['nv']=='Ministro/a' and b['nv']=='Vicepresidencia'):
                a['f']=b['i']; a['nt']='Non atopamos o cesamento no BOE; data de fin tomada do seu nomeamento como '+b['c']+'.'; a['fx']=1; nmov+=1
    print('pechados por novo cargo da mesma persoa',nmov)
    # Adolfo Suárez: primeiro mandato, nomeado o 3/7/1976 (antes do período rastrexado)
    if not any(r['nv']=='Presidencia' and r.get('i','')<'1979' for r in recs):
        recs.append({'n':'Adolfo Suárez González','s':'H','c':'Presidente del Gobierno','nv':'Presidencia','dp':'Presidencia del Gobierno','oi':'nomeamento anterior a 1977 (3 de xullo de 1976)','f':'1979-03-31','dc':'(renovado: Real Decreto 681/1979)'})
    # pechar cargos abertos cando outra persoa é nomeada para o mesmo cargo (mesmo departamento)
    byc=collections.defaultdict(list)
    for r in recs:
        if 'i' in r: byc[(r['dp'] if r['nv']!='Organismos e outros órganos' else '',cargoKey(r))].append(r)
    nsuc=0
    for kk,L in byc.items():
        L.sort(key=lambda r:r['i'])
        for a,b in zip(L,L[1:]):
            if 'f' not in a and norm(a['n'])!=norm(b['n']) and b['i']>a['i']:
                a['f']=b['i']; a['nt']='Non atopamos o cesamento no BOE; data de fin tomada do nomeamento de '+b['n']+'.'; a['fx']=1; nsuc+=1
    # Presidencia do Goberno: un mandato remata co nomeamento do seguinte presidente
    P=sorted([r for r in recs if r['nv']=='Presidencia' and 'i' in r],key=lambda r:r['i'])
    for a,b in zip(P,P[1:]):
        if 'f' not in a: a['f']=b['i']; a['dc']='(renovado: '+(b['dn'] or '')+')'
    # resto (antes de xuño de 2018): fin aproximado co final do goberno en que foron nomeados
    Pi=sorted([r['i'] for r in recs if r['nv']=='Presidencia' and 'i' in r])
    nap=0
    for r in recs:
        if 'f' not in r and 'i' in r and r['i']<'2018-06-01':
            nx=[d for d in Pi if d>r['i']]
            if nx:
                r['f']=nx[0]; r['nt']='Non atopamos o cesamento no BOE; como data de fin aproximada usamos a do nomeamento do seguinte Goberno ('+nx[0]+').'; r['fx']=1; nap+=1
    print('fin aproximado (novo goberno)',nap)
    for r in recs:
        r['c']=re.split(r'\.?\s+Dado en|\.?\s+JUAN CARLOS|\.?\s+FELIPE R|,?\s+(?:y|JI|y\s*,)\s*,?\s*por (?:el|la) que|\s+y pase a ocupar',r['c'])[0].strip(' ,.')
        r['lx']=lxOf(r.get('i'),r.get('f'))
        if r['nv'] in ('Presidencia','Vicepresidencia'): r['dp']='Presidencia del Gobierno'
        elif r['nv']=='Ministro/a':
            m=re.match(r'Ministr[oa] (de|del|para) (.+?)(,| y Vicepresident| y Portavoz|$)',r['c'])
            if m and not re.search(r'sin cartera|Adjunt',r['c']): r['dp']='Ministerio '+m.group(1)+' '+m.group(2)
    print('pechados por sucesor',nsuc)
    return recs
if __name__=='__main__':
    R=build()
    json.dump(R,open('recs.json','w'),ensure_ascii=False)
    c=collections.Counter((r['nv'],'i' in r,'f' in r) for r in R)
    for k,v in sorted(c.items()): print(k,v)
