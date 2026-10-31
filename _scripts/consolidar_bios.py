#!/usr/bin/env python3
"""Consolida nos datos fonte as biografías editadas a man no panel do artifact (colección «bios» da súa base de datos).

  python3 consolidar_bios.py SRC_DIR bios.json [unions.json]

  SRC_DIR   : cartafol cos data*.json (o que se pasa a build_portal_gz.py pack)
  bios.json : {id: {id, n, nl, y, b, u, f, ts}} exportado da colección «bios» (ArtifactData list)
  unions.json (opcional): se a ficha editada foi unida a outra, a biografía vai á que se mantén

Campos da persoa que escribe: nl (lugar de nacemento), y (ano), bx (texto), bxu (ligazón da fonte), bxf (nome da fonte).
Un campo baleiro na edición non cambia o dato existente. Despois de consolidar, reconstrúese o portal e
bórranse da base de datos os documentos consolidados (deixan de facer falta: o dato xa vén nos datos).
"""
import sys, json, glob, os
src, bf = sys.argv[1], sys.argv[2]
bios = json.load(open(bf, encoding='utf-8'))
uni = json.load(open(sys.argv[3], encoding='utf-8')) if len(sys.argv) > 3 else {}
files = sorted(glob.glob(os.path.join(src, 'data*.json')))
D = {f: json.load(open(f, encoding='utf-8')) for f in files}
byid = {}
for f, d in D.items():
    for p in d.get('p') or []:
        byid[p['id']] = (f, p)
done, miss, touched = [], [], set()
for k, b in bios.items():
    pid = str(b.get('id') or k)
    while pid in uni and uni[pid].get('keep') and uni[pid]['keep'] != pid:
        pid = uni[pid]['keep']
    if pid not in byid:
        miss.append(k); continue
    f, p = byid[pid]
    ch = []
    for fld, dst in (('nl', 'nl'), ('y', 'y'), ('b', 'bx'), ('u', 'bxu'), ('f', 'bxf')):
        v = (b.get(fld) or '').strip()
        if v and p.get(dst) != v:
            p[dst] = v; ch.append(dst)
    if ch:
        touched.add(f); done.append((k, pid, p['n'], ch))
for f in touched:
    json.dump(D[f], open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for k, pid, n, ch in done:
    print(f'{k} -> {pid} {n}: {", ".join(ch)}')
print(f'{len(done)} fichas actualizadas; {len(miss)} sen atopar: {miss}')
