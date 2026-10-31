"""Deputación Provincial de Córdoba 2023–2027: integra no rexistro os 27 deputados da sesión constitutiva (30/06/2023)."""
import json, glob, collections, sys
SRC = sys.argv[1]
# nome no acta -> id da persoa (cruzado cos concelleiros electos en 2023 na provincia)
DEP = [  # (nome no acta, id, partido segundo a votación/grupo)
 ('Salvador Fuentes Lopera','216535'),('Narcisa Ruiz Rodríguez','216546'),('Ana Rosa Ruz Carpio','216415'),
 ('Andrés Lorite Lorite','92397'),('Félix Romero Carrillo','216135'),('Miguel A. Torrico Pozuelo','216537'),
 ('Sara Alguacil Roldán','216051'),('M.ª Auxiliadora Moreno Rueda','89666'),('Tatiana Pozo Romero','218655'),
 ('Antonio R. Martín Romero','218092'),('Marta Siles Montes','218541'),('Irene Aguilera Galindo','217465'),
 ('Gabriel Duque Moreno','219226'),('José A. Romero Pérez','216691'),('Esteban Morales Sánchez','218698'),
 ('Desiré Benavides Baena','216387'),('Carmen Pozón Martín-Castaño','218040'),('Salvador Millán Pérez','216443'),
 ('Antonio Oliván Arjona','218990'),('M.ª Auxiliadora Campos Algar','216981'),('José Álvarez Rivas','218890'),
 ('Manuela Martínez Prados','217357'),('Rocío Moyano Adame','217196'),('Rafael Villareal García','218483'),
 ('Irene Ruiz Membrilla','216849'),('José M. Cobo Urbano','219144'),('Yolanda Almagro Alcántara','216564')]
PRES = '216535'; CONST = '2023-06-30'; KEY = '14|2023–2027'
EXP = {'PP':13,'PSOE-A':11,'CON ANDALUCÍA':2,'VOX':1}   # votación da presidencia (13/11/2/1)
files = sorted(glob.glob(SRC+'/data*.json')); D = {f: json.load(open(f)) for f in files}
ids = {i for _, i in DEP}; found = {}
for f, d in D.items():
    for p in d.get('p') or []:
        if p['id'] in ids: found[p['id']] = (f, p)
assert len(found) == 27, ids - set(found)
cnt = collections.Counter()
for nm, i in DEP:
    f, p = found[i]
    p['r'] = [r for r in p['r'] if not (r['t'] == 'D' and r.get('cp') == '14' and r.get('mn') == '2023–2027')]
    src = next((r for r in p['r'] if r['t'] == 'L' and str(r.get('ine','')).startswith('14')), None) or \
          next(r for r in p['r'] if r['t'] == 'M' and r.get('y') == '2023' and str(r.get('ine','')).startswith('14'))
    pa = src.get('pa') or src.get('sg'); cnt[pa] += 1
    r = {'t':'D','e':'Deputación Provincial de Córdoba','pr':'Córdoba','cp':'14','mn':'2023–2027','i':CONST,'pa':pa,
         'ine':src['ine'],'c':'Deputada provincial' if p.get('s') == 'M' else 'Deputado provincial'}
    if i == PRES: r['cg'] = [['Presidente da Deputación', CONST]]
    p['r'].append(r)
assert dict(cnt) == EXP, cnt
# resultados das municipais 2023 na provincia (agrupando as marcas locais de Con Andalucía e do PSOE)
core = next(d for d in D.values() if 'dp' in d)
def grp(sg, name=''):
    u = (sg + ' ' + name).upper().replace('Í', 'I')
    return 'CON ANDALUCÍA' if 'CON ANDALUCIA' in u else 'PSOE-A' if sg.upper() in ('PSOE', 'PSOE-A') else sg
V = collections.Counter(); S = collections.Counter(); NAME = {}
for d in D.values():
    for k, x in (d.get('ml') or {}).items():
        y, ine, _ = k.split('|', 2)
        if y == '2023' and ine.startswith('14'):
            g = grp(x[1], x[0]); V[g] += float(x[2] or 0); S[g] += int(x[3] or 0); NAME.setdefault(g, x[0])
NAME.update({'CON ANDALUCÍA':'Con Andalucía / Izquierda Unida (marcas locais agrupadas)','PSOE-A':'Partido Socialista Obrero Español de Andalucía','PP':'Partido Popular','VOX':'Vox'})
val = sum(r[2] for d in D.values() for k, r in (d.get('mr') or {}).items() if k.startswith('2023|14'))
res = [[g, NAME[g].title() if NAME[g].isupper() else NAME[g], int(v), round(100*v/val, 2), S[g], EXP.get(g, 0)] for g, v in V.most_common() if v/val >= .003 or g in EXP]
core['dp'][KEY] = {'nome':'Deputación Provincial de Córdoba','pr':'Córdoba','mn':'2023–2027','n':27,'constitucion':CONST,'presidente':PRES,
  'membros':[i for _, i in DEP],
  'fontes':['Acta da sesión constitutiva do Pleno da Deputación Provincial de Córdoba, 30/06/2023 (deputados/as que tomaron posesión e elección da presidencia: Salvador Fuentes Lopera, PP, 13 votos en segunda votación)',
            'Ministerio do Interior: resultados das eleccións municipais do 28/05/2023 nos 77 concellos da provincia (partido e concello de cada deputado/a, e totais provinciais)'],
  'nota':'O acta non indica o partido nin o partido xudicial de cada deputado/a: o partido e o concello tómanse da súa candidatura nas municipais de 2023, e o reparto resultante (PP 13, PSOE-A 11, Con Andalucía 2, Vox 1) coincide coa votación da presidencia. Os resultados son o total provincial das municipais do 28/05/2023; as marcas locais de Con Andalucía/IU agrúpanse nunha soa fila.',
  'notas':['O acta escribe «Dª M.ª Auxiliadora Campos Algar»; nas municipais de 2023 (Encinas Reales, PSOE-A) figura como María Dolores Campos Algar, que é a única persoa con eses apelidos electa na provincia.',
           'O acta escribe «Rafael Villareal García»; na candidatura municipal figura como Rafael Villarreal García.'],
  'res':res}
for f, d in D.items(): json.dump(d, open(f, 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', dict(cnt), res[:6])
