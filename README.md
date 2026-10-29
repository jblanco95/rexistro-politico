# Rexistro Político Galego (beta)

Buscador de cargos públicos e candidaturas electorais en Galicia e España: eleccións municipais, autonómicas, xerais e europeas, corporacións locais, deputacións provinciais, Xunta de Galicia e Goberno de España.

Web estática: `index.html` (HTML, CSS e JavaScript nun só ficheiro), `data/` (datos en JSON comprimido con gzip; a extensión `.wasm` é só para que o servidor os entregue sen tocalos) e `fonts/` (tipografías IBM Plex e Source Serif 4, licenza SIL Open Font License).

Os datos proceden de fontes públicas oficiais; a lista completa está ao pé da web. Para informar dun erro, usa o botón «Informar dun erro» da propia web.

## Datos

Os rexistros van en bloques por grupo (`S`: europeas, xerais, autonómicas, gobernos e Senado; `L`: municipais, corporacións, alcaldías e deputacións), período de catro anos e comunidade autónoma. A páxina carga primeiro os supramunicipais do último período, despois os locais do último período e logo cara atrás ata un presuposto de memoria; o resto, cando o pide unha páxina, un filtro ou o botón «Buscar tamén nas anteriores».

- `data/d0-*.wasm`: táboas comúns (concellos, circunscricións, corporacións actuais, deputacións…).
- `data/S2023-es-*.wasm`, `data/L2023-12-*.wasm`…: un bloque (persoas e os seus rexistros dese bloque, e as táboas de resultados dese período).
- `data/xS2023-es-*.wasm`…: índice de busca de cada bloque (binario).
- `data/dir*.wasm`: en que bloques está cada persoa.
- `data/geo-*.wasm`: mapa (TopoJSON).

## Como se xera

Desde a versión do artifact en claude.ai, cos scripts de `_scripts/`:

```bash
python3 _scripts/build_portal_gz.py pack SRC_DIR PUB_DIR
python3 _scripts/make_standalone.py PUB_DIR . _scripts/unions.json
```

- `SRC_DIR`: `index.html` do artifact (`_scripts/artifact/index.html`) e `data.json` + `data2…dataN.json`.
- `PUB_DIR`: versión para o artifact (`index.html` + `data/`); hai que copiar nela `data/geo-*.wasm`.
- `_scripts/unions.json`: unións manuais de fichas feitas no artifact, que aquí se aplican sen base de datos.
- `python3 _scripts/build_portal_gz.py unpack PUB_DIR OUT_DIR` fai o camiño inverso (de `data/` a `data.json` + partes).
