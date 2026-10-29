#!/usr/bin/env python3
"""Xera a versión independente (GitHub Pages) do portal a partir da versión empaquetada para o artifact.

  python3 make_standalone.py PUB_DIR SITE_DIR [unions.json] [--indexar]

  PUB_DIR : saída de build_portal_gz.py pack (index.html + data/*.wasm)
  SITE_DIR: cartafol do repositorio de GitHub Pages (index.html, data/, fonts/, .nojekyll…)
  unions.json (opcional): {id_fusionado: {keep, ...}} — unións manuais feitas no panel do artifact,
            que fóra de claude.ai se aplican desde este ficheiro (non hai base de datos).

Cambios respecto ao artifact:
  - documento HTML completo (doctype, lang="gl", viewport, descrición), sen o envoltorio que
    engade claude.ai se o index.html se descargou da páxina publicada;
  - tipografías servidas desde fonts/ (sen Google Fonts);
  - ligazóns de compartir e de erros co enderezo real da web (location), non o de claude.ai;
  - unións manuais estáticas (sen panel de administración nin revisión de duplicados);
  - franxa «Versión beta» e páxina #aviso-legal; o correo de erros ábrese sen pestana nova.
"""
import sys, os, re, json, shutil, glob

args = [a for a in sys.argv[1:] if not a.startswith('--')]
pub, site = args[0], args[1]
uni = json.load(open(args[2], encoding='utf-8')) if len(args) > 2 else {}
# beta: fóra dos buscadores salvo que se pase --indexar
NOINDEX = '--indexar' not in sys.argv
s = open(os.path.join(pub, 'index.html'), encoding='utf-8').read()
# 0) se o index.html se descargou da páxina publicada, quitar o envoltorio que engade claude.ai
#    (<!doctype html><html><head><meta charset=utf8>…</head><body> … </body></html>): se non, queda duplicado
_w = re.match(r'<!doctype html><html><head><meta charset=utf8>.*?</head><body>\n?', s, re.S | re.I)
if _w:
    s = s[_w.end():].rstrip()
    if s.endswith('</body></html>'):
        s = s[:-len('</body></html>')].rstrip() + '\n'

def rep(old, new, count=1):
    global s
    if old not in s:
        sys.exit(f'non atopo: {old[:80]!r}')
    s = s.replace(old, new, count)

# 1) cabeceira e tipografías
s = re.sub(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">',
           '<link rel="stylesheet" href="fonts/fonts.css">', s)
assert 'fonts.googleapis' not in s
rep('<meta charset="utf-8">',
    '<!doctype html>\n<html lang="gl">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    + ('<meta name="robots" content="noindex, nofollow, noarchive">\n' if NOINDEX else '') +
    '<meta name="description" content="Rexistro Político Galego: cargos públicos e candidaturas en Galicia e España (eleccións municipais, autonómicas, xerais, europeas, deputacións, Xunta e Goberno).">\n'
    '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 rx=%226%22 fill=%22%231f3a4d%22/%3E%3Ctext x=%2216%22 y=%2222%22 font-size=%2216%22 text-anchor=%22middle%22 fill=%22white%22 font-family=%22Georgia,serif%22%3ER%3C/text%3E%3C/svg%3E">')
rep('</style>\n\n<header class="top">',
    # base que no artifact pon o envoltorio de claude.ai: marxes de seguridade, [hidden] e imaxes
    ':root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}\n'
    'html{scroll-padding-top:env(safe-area-inset-top,0px)}\n'
    'body{margin:0;padding:0}\n'
    'img{max-width:100%}\n'
    '[hidden]:not([hidden=until-found i]){display:none!important}\n'
    '.betabar{background:#fff4d6;color:#5a4300;border-bottom:1px solid #ecd9a0;font-size:.82rem}\n'
    '.betabar .wrap{padding-top:6px;padding-bottom:6px}\n'
    '.betabar a{color:inherit}\n'
    '@media (prefers-color-scheme: dark){.betabar{background:#3a3220;color:#f3e3b5;border-bottom-color:#5a4c2a}}\n'
    '.legal h1{margin-bottom:6px}.legal h2{font-size:1rem;margin:20px 0 6px}.legal p,.legal li{max-width:72ch}\n'
    '</style>\n</head>\n<body>\n\n<header class="top">')
rep('<main class="wrap" id="app"></main>',
    '<div class="betabar" role="note"><div class="wrap"><b>Versión beta.</b> Os datos están en revisión e poden conter erros: se atopas algún, <button type="button" class="errbtn" data-err="1" style="padding:1px 8px;font-size:.8rem">infórmanos</button>. <a href="#aviso-legal">Aviso legal e privacidade</a>.</div></div>\n'
    '<main class="wrap" id="app"></main>')
s = s.rstrip() + '\n</body>\n</html>\n'

# 2) ligazóns co enderezo da propia web
s = re.sub(r"const SHARE_BASE='https://claude\.ai/artifact/[^']*';",
           "const SHARE_BASE=location.origin+location.pathname;", s)
# correo de erros: na web propia ábrese na mesma pestana (sen deixar unha pestana baleira)
rep('<a class="btn pri" id="errsend" target="_blank" rel="noopener" aria-disabled="true">',
    '<a class="btn pri" id="errsend" aria-disabled="true">')

# 3) unións estáticas no canto da base de datos de claude.ai
rep("async function initUnions(){\n  if(!window.claude||typeof claude.use!=='function') return;",
    "const STATIC_UNI=" + json.dumps(uni, ensure_ascii=False, separators=(',', ':')) + ";\n"
    "async function initUnions(){\n  if(!window.claude||typeof claude.use!=='function'){ UNI=Object.assign({},STATIC_UNI); if(applyUnions()) route(); return; }")

# 4) aviso legal (#aviso-legal)
AVISO = r'''
function renderAviso(){
  document.title='Aviso legal e privacidade · Rexistro Político Galego';
  app.innerHTML=`<article class="legal"><p><a href="#inicio">← Volver á busca</a></p>
  <h1>Aviso legal e privacidade</h1>
  <p style="color:var(--muted)">Versión beta do Rexistro Político Galego.</p>
  <h2>Que é este sitio</h2>
  <p>O Rexistro Político Galego é un proxecto de investigación e transparencia que recompila, nun único buscador, información pública sobre cargos políticos e candidaturas electorais: eleccións municipais, autonómicas, xerais e europeas, corporacións locais, deputacións provinciais, Xunta de Galicia e Goberno de España. Non é unha fonte oficial nin está vinculado a ningunha administración, partido ou institución citada.</p>
  <h2>Orixe dos datos</h2>
  <p>Todos os datos proceden de fontes públicas: Boletín Oficial do Estado e boletíns provinciais, Ministerio do Interior (Infoelectoral), Parlamento de Galicia, Congreso dos Deputados, Senado, Parlamento Europeo, actas das deputacións provinciais e outras publicacións oficiais. A lista completa de fontes figura ao pé de cada páxina. A información limítase á actividade pública das persoas (candidaturas, cargos, datas, formación política e resultados).</p>
  <h2>Exactitude</h2>
  <p>Os datos uníronse de forma semiautomática a partir de documentos moi diversos (algúns dixitalizados por OCR), polo que poden conter erros de transcrición, homónimos mal unidos ou datos incompletos. Non deben usarse como certificación oficial: para calquera uso con efectos xurídicos consulta a fonte orixinal.</p>
  <h2>Rectificacións e dereitos</h2>
  <p>Se atopas un erro ou queres solicitar a rectificación, actualización ou supresión dun dato que che afecta, podes usar o botón «Informar dun erro» presente en todas as páxinas ou escribir a <a href="mailto:${REPORT_EMAIL}">${REPORT_EMAIL}</a>. Indica a páxina ou ficha e, se é posible, a fonte do dato correcto.</p>
  <h2>Privacidade</h2>
  <p>Este sitio non usa cookies, non ten rexistro de usuarios nin recolle datos de quen o visita. O teu navegador garda unha copia dos ficheiros de datos (almacenamento local) só para acelerar as seguintes visitas; podes borrala desde a configuración do navegador. As mensaxes enviadas co botón de erros envíanse desde o teu propio programa de correo e úsanse só para revisar e corrixir os datos. O sitio está aloxado en GitHub Pages (GitHub, Inc.), que pode rexistrar datos técnicos de acceso, como o enderezo IP, segundo a súa propia política de privacidade.</p>
  </article>`;
  window.scrollTo(0,0);
}
'''
rep("function route(){", AVISO + "function route(){")
rep("  if(h==='revisar') return renderRevisar();\n",
    "  if(h==='aviso-legal') return renderAviso();\n  if(h==='revisar'&&!DBH){ location.hash='#inicio'; return; }\n  if(h==='revisar') return renderRevisar();\n")
# o título volve ao normal fóra do aviso
_rt = "function routeX(){\n  const h=location.hash.slice(1);" if "function routeX(){" in s else "function route(){\n  const h=location.hash.slice(1);"
rep(_rt, _rt + "\n  if(h!=='aviso-legal') document.title='Rexistro Político Galego';")
rep('<p class="errfoot">Atopaches un erro ou un dato incorrecto? <button type="button" class="errbtn" data-err="1">Informar dun erro</button></p>',
    '<p class="errfoot">Atopaches un erro ou un dato incorrecto? <button type="button" class="errbtn" data-err="1">Informar dun erro</button> · <a href="#aviso-legal">Aviso legal e privacidade</a></p>')

# 5) escribir o sitio
os.makedirs(os.path.join(site, 'data'), exist_ok=True)
for f in glob.glob(os.path.join(site, 'data', '*.wasm')):
    os.remove(f)
for f in glob.glob(os.path.join(pub, 'data', '*.wasm')):
    shutil.copy(f, os.path.join(site, 'data'))
open(os.path.join(site, 'index.html'), 'w', encoding='utf-8').write(s)
open(os.path.join(site, '.nojekyll'), 'w').close()
rb = os.path.join(site, 'robots.txt')
if NOINDEX:
    open(rb, 'w').write('User-agent: *\nDisallow: /\n')
elif os.path.exists(rb):
    os.remove(rb)
print('noindex' if NOINDEX else 'indexable', '| ok:', os.path.join(site, 'index.html'), len(s), 'bytes;', len(glob.glob(os.path.join(site, 'data', '*.wasm'))), 'ficheiros de datos;', len(uni), 'unións')
