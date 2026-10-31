# Goberno de España: altos cargos desde 1977

Nomeamentos e ceses dos reais decretos da sección II.A do BOE (Autoridades e persoal — Nomeamentos, situacións e incidencias).

1. `python3 crawl.py 1977-01-01 2026-10-31` descarga os sumarios diarios da API de datos abertos do BOE (`/datosabiertos/api/boe/sumario/AAAAMMDD`) e garda en `raw/AAAA/AAAAMMDD.json` só os títulos da sección II.A. Os días en que a API responde con erro baixan co índice HTML do día: `python3 html_day.py AAAAMMDD`.
2. `python3 build_e.py` extrae os nomeamentos e ceses (`extract.py` para os títulos dunha persoa; `multi.py` para os decretos colectivos, que le do texto XML ou do PDF orixinal), clasifica o cargo e emparella cada nomeamento co seu cese (`recs.json`).
3. `python3 integrate_e.py SRC_DIR DST_DIR` engade os rexistros `E` ás fichas (por nome completo) e valida contra os rexistros existentes desde xuño de 2018.

Cargos incluídos: Presidencia e vicepresidencias do Goberno, ministerios, secretarías de Estado, subsecretarías, secretarías xerais e xerais técnicas, direccións xerais (e cargos con ese rango: gabinetes, direccións adxuntas), delegacións do Goberno, gobernos civís e os principais organismos (Banco de España, CNMV, CNMC, CSN, INE, CSIC, Instituto Cervantes, Fiscalía Xeral, Avogacía Xeral, axencias…). Quedan fóra os cargos militares, xudiciais, diplomáticos, a Casa do Rei e as delegacións para actos concretos.

Cando non se atopa o cese no BOE, o fin do mandato tómase (por esta orde) do renomeamento da mesma persoa, da formación dun novo goberno (ministros), do nomeamento do seguinte titular do mesmo cargo, dun novo alto cargo da mesma persoa ou, en último caso, do nomeamento do seguinte Goberno; en todos eses casos o rexistro leva unha nota que o explica.
