import json,glob,re,collections,sys,os
from parse import split_title,rd_date,norm
MIL=re.compile(r'\b(al|el|del)\s+(Teniente General|General|Almirante|Vicealmirante|Contralmirante|Coronel|Teniente Coronel|Capitán de Navío|General de (Brigada|División)|General Auditor|General Intendente)\b')
ORG=re.compile(r'^(President[ea]|Director[a]?|Director[a]? Ejecutiv[oa]|Gerente|Consejer[oa] Delegad[oa]|Gobernador[a]?|Subgobernador[a]?)\s+(del|de la|de los|de)\s+(Autoridad|Oficina|ICEX|Organismo|Instituto|Agencia|Ente Público|Organismo Autónomo|Consejo de Estado|Consejo Económico y Social|Centro de Investigaciones Sociológicas|Consejo de Seguridad Nuclear|Consejo Superior de Investigaciones Científicas|Radiotelevisión Española|Corporación de Radio y Televisión|Banco de España|Comisión Nacional|Patrimonio Nacional|Fondo Español de Garantía Agraria|Servicio Público de Empleo|Tesorería General|Instituto Cervantes|Centro Nacional de Inteligencia|Centro Superior de Información de la Defensa|Consejo Superior de Deportes|Gabinete de la Presidencia del Gobierno|Gabinete del Presidente del Gobierno|Departamento de Seguridad Nacional|Oficina Económica del Presidente)',re.I)
ORG2=re.compile(r'^(Consejer[oa] (de la Comisión Nacional|del Consejo de Seguridad Nuclear)|Fiscal General del Estado|Abogad[oa] General del Estado|Interventor[a]? General de la Administración del Estado|Alt[oa] Comisionad[oa]|Comisionad[oa]|Portavoz del Gobierno|Jef[ea] del Gabinete del Presidente|Director[a]? del Gabinete del Presidente)',re.I)
def nvOf(c,t):
    c=c.strip(); cl=c.lower()
    if re.search(r'casa de (su majestad|s\. ?m\.)|que asistir|asistirá|ceremonia|misión extraordinaria|misión especial|toma de posesión|funeral|consistorio|beatificaci|canonizaci|en representación de españa|delegación española',cl): return None
    if re.match(r'^(el\s+)?president[ea] del gobierno$',cl): return 'Presidencia'
    if re.match(r'^vicepresident[ea] (primer[oa] |segund[oa] |tercer[oa] |cuart[oa] )?del gobierno',cl): return 'Ministro/a' if re.search(r'\by ministr',cl) else 'Vicepresidencia'
    if re.match(r'^ministr[oa] (de |del |para |sin cartera|adjunt|portavoz)',cl) and not re.search(r'plenipotenciario|consejero|tribunal',cl): return 'Ministro/a'
    if re.match(r'^secretari[oa] de estado',cl): return 'Secretaría de Estado'
    if re.match(r'^subsecretari[oa]\b',cl): return 'Subsecretaría'
    if re.match(r'^secretari[oa] general t[eé]cnic',cl): return 'Secretaría xeral técnica'
    if re.match(r'^secretari[oa] general\b',cl) and not re.search(r'gobierno civil|casa de su majestad|delegaci[oó]n|consejo de administraci|ej[eé]rcito|marina|del aire|jefatura|patronato|direcci[oó]n general|fondo de|consejo superior de investigaciones|armada|guardia civil',cl): return 'Secretaría xeral'
    if re.match(r'^director[a]? general\b',cl): return 'Dirección xeral'
    if re.match(r'^director[a]? (adjunt[oa] )?del (gabinete|departamento)\b',cl) or re.match(r'^director[a]? adjunt[oa]\b',cl): return 'Dirección xeral'
    if re.match(r'^delegad[oa] del gobierno\b',cl):
        if re.search(r'confederaci|«|sociedad|compañ|puerto|campsa|comisi[oó]n de planeamiento|canalizaci|mancomunidad|telef[oó]nica|tabacalera|isla de|autopistas|banco|caja|s\. ?a\.|empresa|renfe|iberia',cl): return None
        return 'Delegación do Goberno'
    if re.match(r'^gobernador[a]? civil\b',cl): return 'Goberno civil'
    if MIL.search(t): return None
    if ORG.match(c) or ORG2.match(c): return 'Organismos e outros órganos'
    return None
TITLEC={'de','del','la','las','los','y','e','para','en','el','a','con','sin','por'}
def tcase(s):
    w=s.lower().split(' '); return ' '.join(x if (x in TITLEC and i) else x[:1].upper()+x[1:] for i,x in enumerate(w))
def depOf(dep):
    d=tcase(dep or '')
    return d.replace('Ministerio De ','Ministerio de ')
def events(years=None):
    ev=[]; bad=collections.Counter(); multi=[]
    for f in sorted(glob.glob('raw/*/*.json')):
        day=os.path.basename(f)[:8]
        if years and day[:4] not in years: continue
        for it in json.load(open(f)) or []:
            t=(it.get('t') or '').strip()
            if not re.match(r'(Real )?Decreto',t): continue
            dn,dd=rd_date(t)
            r=split_title(t)
            if not r: continue
            kind,names,cargo,body=r
            if len(names)!=1:
                if not MIL.search(t): multi.append((day,it['id'],it['dep'],t))
                continue
            c=re.sub(r'^(del|de la|de los|el|la)\s+','',cargo).strip(' ,.')
            c=re.split(r'\s+y por (?:el|la) que |\.\s+Se nombra|,?\s+y se dispone ',c)[0].strip(' ,.')
            nv=nvOf(c,t)
            if not nv or ',' in names[0][0]: continue
            pub=f'{day[:4]}-{day[4:6]}-{day[6:]}'
            ev.append({'k':kind,'n':names[0][0],'s':names[0][1],'c':c[:1].upper()+c[1:],'nv':nv,'dep':depOf(it['dep']),'d':dd or pub,'pub':pub,'dn':dn,'u':it.get('u') or f"https://www.boe.es/diario_boe/txt.php?id={it['id']}",'id':it['id'],'t':t})
    return ev,multi
if __name__=='__main__':
    ys=set(sys.argv[1].split(',')) if len(sys.argv)>1 else None
    ev,multi=events(ys)
    print(len(ev),collections.Counter((e['k'],e['nv']) for e in ev))
    print('multi',len(multi)); [print(' ',m) for m in multi[:15]]
    json.dump(ev,open('events.json','w'),ensure_ascii=False)
