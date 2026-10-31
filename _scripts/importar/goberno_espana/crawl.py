import json,os,sys,time,datetime,urllib.request,concurrent.futures as cf,threading
OUT='raw'; os.makedirs(OUT,exist_ok=True)
lock=threading.Lock()
def items(d):
    out=[]
    for di in (d.get('data',{}).get('sumario',{}).get('diario') or []):
        secs=di.get('seccion',[]); secs=secs if isinstance(secs,list) else [secs]
        for sec in secs:
            if not str(sec.get('codigo','')).startswith('2A'): continue
            if isinstance(sec.get('texto'),dict): sec={**sec,**sec['texto']}
            deps=sec.get('departamento',[]); deps=deps if isinstance(deps,list) else [deps]
            for dep in deps:
                if isinstance(dep.get('texto'),dict): dep={**dep,**dep['texto']}
                eps=dep.get('epigrafe',[]); eps=eps if isinstance(eps,list) else [eps]
                groups=[(ep.get('nombre',''),ep.get('item',[])) for ep in eps]+[('',dep.get('item',[]))]
                for en,its in groups:
                    its=its if isinstance(its,list) else [its]
                    for it in its:
                        if not it: continue
                        u=it.get('url_html') or ''; u=u if isinstance(u,str) else u.get('texto','')
                        out.append({'id':it.get('identificador'),'dep':dep.get('nombre'),'ep':en,'t':it.get('titulo'),'u':u})
    return out
def get(day):
    fn=f'{OUT}/{day[:4]}/{day}.json'
    if os.path.exists(fn): return 'skip'
    url=f'https://www.boe.es/datosabiertos/api/boe/sumario/{day}'
    for k in range(6):
        try:
            req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'rexistro-politico (investigacion)'})
            with urllib.request.urlopen(req,timeout=60) as r: d=json.load(r)
            res=items(d); break
        except urllib.error.HTTPError as e:
            if e.code==404: res=None; break
            time.sleep(2**k)
        except Exception as e:
            time.sleep(2**k)
    else:
        return 'fail'
    os.makedirs(os.path.dirname(fn),exist_ok=True)
    json.dump(res,open(fn,'w'),ensure_ascii=False)
    return 'ok' if res is not None else 'none'
a=datetime.date(*map(int,sys.argv[1].split('-'))); b=datetime.date(*map(int,sys.argv[2].split('-')))
days=[(a+datetime.timedelta(i)).strftime('%Y%m%d') for i in range((b-a).days+1)]
c={}; t0=time.time()
with cf.ThreadPoolExecutor(4) as ex:
    for i,r in enumerate(ex.map(get,days)):
        c[r]=c.get(r,0)+1
        if i%500==0: print(days[i],c,round(time.time()-t0),flush=True)
print('FIN',c,round(time.time()-t0),flush=True)
