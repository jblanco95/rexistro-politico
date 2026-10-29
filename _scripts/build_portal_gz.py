#!/usr/bin/env python3
"""Empaqueta o portal para publicar con carga rápida (desde v52).

  python3 build_portal_gz.py pack   SRC_DIR OUT_DIR
      SRC_DIR: index.html + data.json (+ partes data2..dataN.json, formato v51)
      OUT_DIR: index.html (co MANIFEST actualizado) + data/*.wasm (gzip)

  python3 build_portal_gz.py unpack PUB_DIR OUT_DIR
      Fai o camiño inverso: dos .gz publicados volve a data.json + dataN.json
      (formato v51, ≤ 9 MB por parte), para seguir usando os scripts de sempre.
      Le tanto os paquetes por bloques (v105) coma os de núcleo + resto (v52–v104).

Bloques (desde v105): os rexistros repártense por (grupo, período, rexión) — ver Units:
  S = europeas, xerais, autonómicas, gobernos e Senado; L = municipais, corporacións,
  alcaldías e deputacións; período de catro anos (ciclo municipal); rexión = comunidade
  autónoma nos L. A páxina carga primeiro S e despois L do último período, e logo cara
  atrás ata un presuposto; o resto, cando o pide unha páxina. Para engadir as municipais
  de toda España doutros anos abonda con incluílas nos datos: saen bloques L novos.
  Cada persoa vai en todos os bloques onde ten rexistros (cos seus datos e só eses
  rexistros); dir*.wasm di, para cada ID, en que bloques está.
Os nomes dos .gz levan un hash do contido: se o ficheiro non cambia, o navegador
reutiliza a copia gardada (IndexedDB) e non o volve descargar.

Índice de busca precalculado (desde v103): un x*.wasm por bloque, binario, cos textos de
busca, a puntuación e a orde por nome de cada persoa, e o reconto de partidos do
despregable sen filtros (desde v104). Antes calculábao o navegador en cada visita
(indexPerson, sortP); agora só o le. Ver build_index() e PartyCounts.
"""
import gzip, hashlib, json, os, re, struct, sys, glob, unicodedata

GAL = {'15', '27', '32', '36'}
DROP_FALSE = ('si', 'hom', 'mv', 'fz')   # só se le se son certos (p.si, p.hom…)


def load_src(src):
    d = json.load(open(os.path.join(src, 'data.json'), encoding='utf-8'))
    persons = list(d.pop('p'))
    for f in d.pop('parts', []) or []:
        persons += json.load(open(os.path.join(src, f), encoding='utf-8'))['p']
    return d, persons


def is_rest(p):
    return bool(p['r']) and all(r['t'] in 'MLA' and r.get('ine') and r['ine'][:2] not in GAL for r in p['r'])


def slim(p):
    for k in DROP_FALSE:
        if k in p and p[k] is False:
            del p[k]
    return p


# ---- índice de busca: mesmo resultado que indexPerson()/score() do index.html de v102 ----
# Se cambia a busca no index.html (textos fixos, campos), hai que cambiala tamén aquí.

def norm(s):
    """= norm() do index.html: sen acentos, maiúsculas, só A-Z 0-9 e espazos simples."""
    s = unicodedata.normalize('NFD', s or '')
    s = re.sub('[̀-ͯ]', '', s).upper()
    s = re.sub('[^A-Z0-9 ]', ' ', s)
    return re.sub(' +', ' ', s).strip(' ')


RANK_LOCAL = {'Alcalde': 0, 'Alcalde en Funciones': 0, 'Presidente Gestor': 0,
              'Teniente de Alcalde': 1, 'Vocal gestor': 2, 'Concejal': 2}


def cargo_local(c, s):
    F = s == 'M'
    return {'Concejal': 'Concelleira' if F else 'Concelleiro', 'Alcalde': 'Alcaldesa' if F else 'Alcalde',
            'Teniente de Alcalde': 'Tenenta de alcalde' if F else 'Tenente de alcalde',
            'Vocal gestor': 'Vogal xestora' if F else 'Vogal xestor',
            'Presidente Gestor': 'Presidenta xestora' if F else 'Presidente xestor',
            'Alcalde en Funciones': 'Alcaldesa en funcións' if F else 'Alcalde en funcións'}.get(c, c)


def glist_of(html):
    """GLIST (eleccións xerais) tal como está no index.html, para que glab(gk(r)) coincida."""
    m = re.search(r"const GLIST=(\[.*?\]);", html)
    if not m:
        sys.exit('index.html sen a liña "const GLIST=[...];"')
    return json.loads(m.group(1).replace("'", '"'))


def search_bits(p, r, gbyd):
    """Textos de busca dun rexistro (= bits de indexPerson), cos campos que engade prepRec."""
    t, g = r['t'], r.get
    d = str(g('d') or '')

    def glab_gk():
        k = gbyd.get(d) or d[:4]
        return '2019 (abril)' if k == '2019A' else '2019 (novembro)' if k == '2019N' else k
    o = lambda k: g(k) or ''
    pt = g('pt')
    return [g('c'), g('m'), g('pr'), g('pa'), g('sg'), g('ca'), g('dp'), g('nv'), g('pi'), g('al'),
            cargo_local(g('c'), p.get('s')) if t == 'L' else '',
            ('candidato candidata parlamento ' + d[:4] + (' parlament catalunya cataluna diputat diputada deputado deputada'
             if g('e') == 'Parlament de Catalunya' else '')) if t == 'C' else '',
            'xunta goberno' if t == 'X' else '',
            'goberno autonomico gobierno ' + o('ins') + ' ' + o('cc') if t == 'K' else '',
            'senado senador senadora designado designada designacion autonomica ' + o('ca') if t == 'S' else '',
            ('senado senador senadora ' + ('designado designada designacion autonomica ' if pt == 'D' else
             'designacion real ' if pt == 'R' else 'electo electa ') + o('lu') + ' ' + o('gr') + ' ' + o('sg')) if t == 'Q' else '',
            'congreso deputado deputada xerais ' + d[:4] + ' ' + glab_gk() if t == 'G' else '',
            'senado senador senadora xerais ' + d[:4] + ' ' + glab_gk() if t == 'N' else '',
            'europeas parlamento europeo eurodeputado eurodeputada ' + d[:4] if t == 'U' else '',
            'alcalde alcaldesa mandato ' + str(g('mn') or '').replace('–', ' ', 1) + ' ' + o('ls') if t == 'A' else '',
            ('deputacion deputación provincial deputado deputada ' + o('px') + ' ' + ' '.join(x[0] for x in g('cg') or []))
            if t == 'D' else '',
            ('municipais ' + g('y') + ' candidato candidata ' + ('concelleiro concelleira electo electa' if g('el') else ''))
            if t == 'M' else '',
            o('sn')]


def score(p):
    """Puntuación de relevancia nos resultados (= score() do index.html ata v104): vai no índice."""
    s = 0
    for r in p['r']:
        t, g = r['t'], r.get
        if t == 'X': s = max(s, 40 if g('f') else {'Presidencia': 100, 'Conselleiro/a': 90}.get(g('nv')) or 70)
        if t == 'K': s = max(s, 38 if g('f') else {'Presidencia': 100, 'Vicepresidencia': 90, 'Consejero/a': 88}.get(g('nv')) or 66)
        if t == 'E': s = max(s, 45 if g('f') else {'Presidencia': 110, 'Ministro/a': 95, 'Secretaría de Estado': 85}.get(g('nv')) or 72)
        if t == 'G': s = max(s, 65 if g('el') else 10)
        if t == 'N': s = max(s, 62 if g('el') else 10)
        if t in 'QS': s = max(s, 62)
        if t == 'U': s = max(s, 64 if g('el') else 3)
        if t == 'C': s = max(s, (60 if str(g('d')) > '2024' else 55) if g('el') else 10)
        if t == 'L': s = max(s, {0: 50, 1: 20, 2: 5}[RANK_LOCAL[g('c')]])
        if t == 'M': s = max(s, (6 if g('y') == '2023' else 4) if g('el') else 1)
        if t == 'A': s = max(s, 45)
        if t == 'D':
            cg = [x[0] for x in g('cg') or []]
            s = max(s, 75 if any(re.match('Presidente', x) for x in cg) else 58 if any(re.match('Vicepresident', x) for x in cg) else 48)
    return s


AMB_T = 'UGNXCLMDKAQSE'   # bit de cada tipo de rexistro en p._a (= AMB_T do index.html)
LOCAL_T = 'MLAD'          # rexistros locais (bloques L); o resto son supramunicipais (bloques S)
MAX_ENTRIES = 25_000      # persoas por ficheiro de bloque, como máximo (os grandes pártense: cada JSON.parse bloquea menos)
DIR_PER_FILE = 20_000     # persoas por ficheiro do directorio, aproximadamente


def name_ranks(parts):
    """Posición do nome normalizado na orde alfabética (mesmo número = mesmo nome), común a todo."""
    nn = sorted({norm(p['n']) for persons in parts for p in persons})
    return {k: i for i, k in enumerate(nn)}


def js_const(html, name):
    """Valor dunha constante do index.html (const NAME=…;), para usar as mesmas táboas ca a páxina."""
    m = re.search(r'const ' + name + r'=(.+?);\s*$', html, re.M)
    if not m:
        sys.exit(f'index.html sen a liña "const {name}=…;"')
    return json.loads(m.group(1).replace("'", '"'))


# ---- bloques: (grupo, período, rexión) ----
# grupo S (europeas, xerais, autonómicas, gobernos, Senado) ou L (municipais, corporacións, alcaldías, deputacións);
# período: ciclo municipal de catro anos (2023 = 2023–2026; antes de 1979, 1975); rexión: comunidade autónoma
# (código INE) nos L, 'es' nos S. Cárganse do máis recente ao máis antigo, S antes ca L.

def period(y):
    y = int(y)
    return 1975 if y < 1979 else 1979 + 4 * ((y - 1979) // 4)


class Units:
    def __init__(self, html):
        self.pr_ca = js_const(html, 'PR_CA')
        self.legs = {'X': dict(js_const(html, 'LEGS')), 'E': dict(js_const(html, 'LEGS_E'))}
        self.klex = {ca: dict(v) for ca, v in js_const(html, 'KLEX').items()}

    def year(self, r):
        """Ano do rexistro (para o período): elección, toma de posesión ou inicio do mandato/lexislatura."""
        t, g = r['t'], r.get
        if t == 'M':
            return g('y')
        if t in 'GNCUL':
            return str(g('d') or '')[:4] or None
        if t in 'AD':
            return str(g('mn') or '')[:4] or None
        if g('i'):
            return str(g('i'))[:4]
        if t == 'Q' and g('k'):
            return str(g('k'))[:4]
        lx = str(g('lx') or '').split('–')[0]
        d = (self.klex.get(g('cc'), {}) if t == 'K' else self.legs.get(t, {})).get(lx)
        return d[:4] if d else None

    def key(self, r, latest):
        y = self.year(r)
        p = period(y) if y and y.isdigit() else latest
        if r['t'] in LOCAL_T:
            cp = r.get('cp') or str(r.get('ine') or '')[:2]
            return ('L', p, self.pr_ca.get(cp, '00'))
        return ('S', p, 'es')


def unit_order(k):
    g, p, rg = k
    return (-p, g != 'S', rg != '12', rg)   # máis recente primeiro; S antes ca L; Galicia primeiro


def table_units(d, units):
    """Táboas de resultados por bloque: as de cada ano van co bloque dese período (e rexión, nas locais)."""
    pr_ca = units.pr_ca
    T = {}
    put = lambda k, name, key, v: T.setdefault(k, {}).setdefault(name, {}).__setitem__(key, v)
    for name in ('ml', 'mr'):
        for key, v in (d.get(name) or {}).items():
            y, ine = key.split('|')[:2]
            put(('L', period(y), pr_ca.get(ine[:2], '00')), name, key, v)
    for y, byine in (d.get('corpE') or {}).items():
        for ine, ids in byine.items():
            T.setdefault(('L', period(y), pr_ca.get(ine[:2], '00')), {}).setdefault('corpE', {}).setdefault(y, {})[ine] = ids
    for name in ('ar', 'gr', 'nr', 'ur'):
        for key, v in (d.get(name) or {}).items():
            put(('S', period(key[:4]), 'es'), name, key, v)
    return T


TABLES = ('ml', 'mr', 'corpE', 'ar', 'gr', 'nr', 'ur')


def rparts(r, ml):
    """= rparts() do index.html (partidos dun rexistro para o despregable), cos campos de prepRec."""
    sn = r.get('sn')
    if r['t'] == 'M':
        sn = (ml.get(f"{r['y']}|{r['ine']}|{r['sg']}") or [None, None])[1]
    return [x.upper() for x in (r.get('pa') or r.get('sg'), sn, r.get('ls') if r['t'] == 'A' else None) if x]


def js_entries_order(cnt, first):
    """Orde de Object.entries: claves numéricas en orde numérica e despois as outras na orde de aparición."""
    idx = lambda k: re.fullmatch(r'0|[1-9]\d*', k) and int(k) < 2**32 - 1
    return sorted((k for k in cnt if idx(k)), key=int) + sorted((k for k in cnt if not idx(k)), key=lambda k: first[k])


class PartyCounts:
    """= optionList0() do index.html sen filtros, tras cargar os bloques 0..k (un reconto por bloque):
    [[partido, nº de persoas], …] cos de 15 ou máis, na orde do despregable. Incremental: cada persoa só
    se revisa cando chegan rexistros seus. A orde de aparición é a de P (puntuación, nome, desempate)."""
    def __init__(self, ml, ranks, seq, gscore):
        self.ml, self.ranks, self.seq, self.gscore = ml, ranks, seq, gscore
        self.S, self.cnt, self.first = {}, {}, {}   # por persoa: partidos; por partido: nº e 1ª aparición

    def add(self, entry):
        pid = entry['id']
        S = self.S.setdefault(pid, {})   # partido -> posición na ficha
        key = (-self.gscore[pid], self.ranks[norm(entry['n'])], self.seq[pid])
        # partidos na orde dos rexistros (ri: posición orixinal na ficha), como os percorre a páxina
        for n, r in enumerate(entry['r']):
            for m, x in enumerate(rparts(r, self.ml)):
                if x in S:
                    continue
                S[x] = (r.get('ri', n), m)
                k = key + (S[x],)
                if x not in self.first or k < self.first[x]:
                    self.first[x] = k
                self.cnt[x] = self.cnt.get(x, 0) + 1

    def snapshot(self):
        keys = js_entries_order(self.cnt, self.first)
        return sorted(([k, self.cnt[k]] for k in keys if self.cnt[k] >= 15), key=lambda x: -x[1])


def build_index(entries, d, html, ranks, seq, gscore, gamb, extra):
    """Índice binario dun bloque, coas persoas na mesma orde ca no seu ficheiro.
    Cada rexistro dá uns textos de busca; os rexistros cos mesmos textos (por exemplo, os
    candidatos dunha mesma lista municipal) comparten grupo. Formato (little-endian):
         'RPX4', u32 nP, nG (grupos), nT (textos), nPG, nGT, bytes do dicionario, bytes do JSON
         u32 orde do nome[nP]   u32 desempate (só nomes repetidos; se non, 0)[nP]   u32 grupos de cada persoa[nPG]
         u16 textos de cada grupo[nGT]    u16 tipos de rexistro (bits AMB_T)[nP]
         u8  puntuación[nP]               u8  nº de grupos por persoa[nP]   u8 nº de textos por grupo[nG]
         dicionario: textos normalizados separados por \n
         JSON (extra): {"pc": reconto de partidos sen filtros tras cargar ata este bloque (PartyCounts)}
    Puntuación e tipos son os da persoa con todos os seus rexistros: a orde e o resumo da busca
    non dependen do que estea cargado.
    A orde dos resultados (sortP) sae de puntuación + orde do nome + desempate (= orde de carga de v104).
    Os nomes (p.n, p.alt) non van no dicionario: normalízaos o navegador en segundo plano.
    Unha palabra buscada coincide se está dentro do nome ou dalgún texto (= p._k.includes de v102)."""
    cn, ml = d.get('cn', {}), d.get('ml', {})
    gbyd = {x[1]: x[0] for x in glist_of(html)}
    txt, grp, pg, pc = {}, {}, [], []
    for p in entries:
        gs = []
        for r in p['r']:
            if r.get('ine') and r['t'] in 'LMA':
                c = cn.get(r['ine']) or []
                r = dict(r, m=c[0] if c else None, pr=c[1] if len(c) > 1 else None)
            if r['t'] == 'M':
                l = ml.get(f"{r['y']}|{r['ine']}|{r['sg']}") or []
                r = dict(r, ca=l[0] if l else None, sn=l[1] if len(l) > 1 else None)
            tt = tuple(txt.setdefault(x, len(txt)) for x in dict.fromkeys(norm(b) for b in search_bits(p, r, gbyd) if b) if x)
            gs.append(grp.setdefault(tt, len(grp)))
        gs = list(dict.fromkeys(gs))
        pg += gs; pc.append(len(gs))
    gt = [t for g in grp for t in g]
    gc = [len(g) for g in grp]
    if len(txt) > 65535 or max(pc + gc, default=0) > 255:
        sys.exit('índice: demasiados textos ou grupos para o formato RPX4')
    db = '\n'.join(txt).encode('ascii')
    xj = json.dumps(extra, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    n = len(entries)
    return (b'RPX4' + struct.pack('<7I', n, len(grp), len(txt), len(pg), len(gt), len(db), len(xj)) +
            struct.pack(f'<{n}I', *(ranks[norm(p['n'])] for p in entries)) +
            struct.pack(f'<{n}I', *(seq[p['id']] for p in entries)) + struct.pack(f'<{len(pg)}I', *pg) +
            struct.pack(f'<{len(gt)}H', *gt) + struct.pack(f'<{n}H', *(gamb[p['id']] for p in entries)) +
            bytes(gscore[p['id']] for p in entries) + bytes(pc) + bytes(gc) + db + xj)


def id_bucket(pid, nb):
    """= idBucket() do index.html: ficheiro do directorio onde está unha persoa."""
    h = 0
    for c in pid:
        h = (h * 31 + ord(c)) & 0xffffffff
    return h % nb


def gz_write(out, name, obj):
    raw = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    data = gzip.compress(raw, compresslevel=9, mtime=0)
    h = hashlib.sha1(data).hexdigest()[:10]
    fn = f'data/{name}-{h}.wasm'   # binario gzip; .wasm porque o servidor de artifacts non serve .gz
    with open(os.path.join(out, fn), 'wb') as f:
        f.write(data)
    return fn, len(raw), len(data)


def strip_wrapper(html):
    """Quita o envoltorio que engade claude.ai ao servir o artifact (<!doctype html><html><head>
    <meta charset=utf8>…</head><body> … </body></html>), se o index.html se descargou da páxina
    publicada: ao volver publicalo, o artifact engádeo outra vez e quedaría duplicado."""
    m = re.match(r'<!doctype html><html><head><meta charset=utf8>.*?</head><body>\n?', html, re.S | re.I)
    if not m:
        return html
    html = html[m.end():].rstrip()
    return html[:-len('</body></html>')].rstrip() + '\n' if html.endswith('</body></html>') else html + '\n'


def pack(src, out):
    os.makedirs(os.path.join(out, 'data'), exist_ok=True)
    # só os ficheiros que xera pack (o mapa geo-*.wasm non se toca)
    for old in glob.glob(os.path.join(out, 'data', '*.wasm')) + glob.glob(os.path.join(out, 'data', '*.gz')):
        if re.match(r'(d0|core\d+|rest\d+|ix\d+|[SL]\d{4}-\w+|x[SL]\d{4}-\w+|dir\d+)-[0-9a-f]+\.(wasm|gz)$', os.path.basename(old)):
            os.remove(old)
    html = strip_wrapper(open(os.path.join(src, 'index.html'), encoding='utf-8').read())
    d, persons = load_src(src)
    persons = [slim(p) for p in persons]
    U = Units(html)
    latest = max(period(y) for p in persons for r in p['r'] for y in [U.year(r)] if y and y.isdigit())
    ranks = name_ranks((persons,))
    # desempate na orde: a orde de carga de v52–v104 (núcleo antes có resto; dentro, a do ficheiro)
    seq = {p['id']: i for i, p in enumerate(sorted(persons, key=is_rest))}
    # no índice só fai falta para os nomes repetidos (os demais nunca empatan): 0 para o resto, que comprime mellor
    nn_n = {}
    for p in persons:
        k = norm(p['n']); nn_n[k] = nn_n.get(k, 0) + 1
    seq_ix = {p['id']: seq[p['id']] if nn_n[norm(p['n'])] > 1 else 0 for p in persons}
    # cada persoa vai a todos os bloques onde ten rexistros, cos seus datos completos e só os rexistros dese bloque
    # (ri = posición orixinal do rexistro, para que a páxina os volva poñer na mesma orde)
    by = {}
    home = {}
    for p in persons:
        groups = {}
        for i, r in enumerate(p['r']):
            groups.setdefault(U.key(r, latest), []).append((i, r))
        if not groups:
            groups[('S', latest, 'es')] = []
        split = len(groups) > 1
        base = {k: v for k, v in p.items() if k != 'r'}
        for k, rs in groups.items():
            by.setdefault(k, []).append(dict(base, r=[dict(r, ri=i) if split else r for i, r in rs]))
        home[p['id']] = list(groups)
    T = table_units(d, U)
    keys = sorted(set(by) | set(T), key=unit_order)
    # ficheiros: os bloques grandes pártense en anacos de MAX_ENTRIES persoas
    files = []
    for k in keys:
        es = by.get(k, [])
        parts = [es[i:i + MAX_ENTRIES] for i in range(0, len(es), MAX_ENTRIES)] or [[]]
        for j, ch in enumerate(parts):
            files.append((k, j, ch, T.get(k, {}) if j == 0 else {}))
    base = {k: v for k, v in d.items() if k not in TABLES}
    my = {}
    for key in (d.get('mr') or {}):
        y, ine = key.split('|')[:2]
        my.setdefault(ine, []).append(y)
    base['_my'] = {ine: sorted(ys) for ine, ys in my.items()}   # anos con resultados municipais de cada concello
    man = {'u': [], 'dir': []}
    tot_raw = tot_gz = 0
    fn, a, b = gz_write(out, 'd0', base); man['d0'] = fn; tot_raw += a; tot_gz += b
    print(f'{fn}: {a/1e6:.1f} MB -> {b/1e6:.2f} MB (táboas comúns)')
    gscore = {p['id']: score(p) for p in persons}
    gamb = {p['id']: sum(1 << AMB_T.index(t) for t in {r['t'] for r in p['r']}) for p in persons}
    pcs = PartyCounts(d.get('ml', {}), ranks, seq, gscore)
    uix = {}
    for n, (k, j, ch, tabs) in enumerate(files):
        g, per, rg = k
        name = f'{g}{per}-{rg}' + (chr(97 + j) if j else '')
        fd, a1, b1 = gz_write(out, name, {'p': ch, 't': tabs})
        for e in ch:
            pcs.add(e)
        fx, a2, b2 = gz_write(out, 'x' + name, build_index(ch, d, html, ranks, seq_ix, gscore, gamb, {'pc': pcs.snapshot()}))
        nr = sum(len(e['r']) for e in ch)
        man['u'].append({'f': fd, 'x': fx, 'n': len(ch), 'r': nr, 'g': g, 'y': per, 'rg': rg})
        for e in ch:
            uix.setdefault(e['id'], []).append(n)
        tot_raw += a1 + a2; tot_gz += b1 + b2
        print(f'{fd}: {len(ch)} persoas, {nr} rexistros, {(a1+a2)/1e6:.1f} MB -> {(b1+b2)/1e6:.2f} MB (con índice)')
    # directorio: en que bloques ten rexistros cada persoa (para abrir unha ficha sen cargalo todo)
    nb = 1
    while nb * DIR_PER_FILE < len(uix):
        nb *= 2
    buckets = [{} for _ in range(nb)]
    for pid, us in uix.items():
        buckets[id_bucket(pid, nb)][pid] = us
    for i, bk in enumerate(buckets):
        fn, a, b = gz_write(out, f'dir{i}', bk); man['dir'].append(fn); tot_raw += a; tot_gz += b
    print(f'directorio: {nb} ficheiros')
    man['v'] = hashlib.sha1(json.dumps(man, sort_keys=True).encode()).hexdigest()[:10]
    line = 'const MANIFEST=' + json.dumps(man, separators=(',', ':')) + ';'
    html, n = re.subn(r'const MANIFEST=\{.*?\};', lambda m: line, html, count=1)
    if n != 1:
        sys.exit('index.html sen a liña "const MANIFEST={...};" (usar o index.html de v52 ou posterior)')
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
    print(f'{len(persons)} persoas en {len(files)} ficheiros de bloque; '
          f'{tot_raw/1e6:.1f} MB -> {tot_gz/1e6:.2f} MB comprimido; MANIFEST v={man["v"]}')
    return man


def unpack(pub, out, max_bytes=9_000_000):
    html = open(os.path.join(pub, 'index.html'), encoding='utf-8').read()
    man = json.loads(re.search(r'const MANIFEST=(\{.*?\});', html).group(1))
    rd = lambda f: json.loads(gzip.decompress(open(os.path.join(pub, f), 'rb').read()))
    d = rd(man['d0'])
    d.pop('_my', None)
    byid = {}
    if 'u' in man:   # v105: bloques
        for u in man['u']:
            j = rd(u['f'])
            for name, tab in j['t'].items():
                if name == 'corpE':
                    for y, v in tab.items():
                        d.setdefault('corpE', {}).setdefault(y, {}).update(v)
                else:
                    d.setdefault(name, {}).update(tab)
            for e in j['p']:
                p = byid.setdefault(e['id'], dict(e, r=[]))
                p['r'] += e['r']
        for p in byid.values():
            if any('ri' in r for r in p['r']):
                p['r'] = [{k: v for k, v in r.items() if k != 'ri'} for r in sorted(p['r'], key=lambda r: r['ri'])]
        persons = list(byid.values())
    else:            # v52–v104: núcleo + resto
        persons = []
        for f in man['core'] + man['rest']:
            persons += rd(f)['p']
    persons.sort(key=lambda p: int(p['id']))   # si/hom/mv/fz ausentes = False
    os.makedirs(out, exist_ok=True)
    parts, cur, size = [], [], 0
    for p in persons:
        s = len(json.dumps(p, ensure_ascii=False)) + 2
        if cur and size + s > max_bytes:
            parts.append(cur); cur, size = [], 0
        cur.append(p); size += s
    parts.append(cur)
    head = dict(d); head['p'] = parts[0]
    head['parts'] = [f'data{i}.json' for i in range(2, len(parts) + 1)]
    json.dump(head, open(os.path.join(out, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for i, ch in enumerate(parts[1:], 2):
        json.dump({'p': ch}, open(os.path.join(out, f'data{i}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
    print(f'{len(persons)} persoas -> data.json + {len(parts)-1} partes en {out}')


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in ('pack', 'unpack'):
        sys.exit(__doc__)
    (pack if sys.argv[1] == 'pack' else unpack)(sys.argv[2], sys.argv[3])
