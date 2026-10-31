import re,json,os,sys,urllib.request,html as H
def fetch_day(day):
    y,m,d=day[:4],day[4:6],day[6:]
    t=urllib.request.urlopen(urllib.request.Request(f'https://www.boe.es/boe/dias/{y}/{m}/{d}/',headers={'User-Agent':'rexistro-politico (investigacion)'}),timeout=60).read().decode('utf8','replace')
    out=[]; sec=''; dep=''; ep=''
    for m_ in re.finditer(r'<h3[^>]*>(.*?)</h3>|<h4[^>]*>(.*?)</h4>|<h5[^>]*>(.*?)</h5>|<li class="dispo">\s*<p>(.*?)</p>(.*?)</li>\s*</ul>',t,re.S):
        if m_.group(1): sec=H.unescape(re.sub('<[^>]+>','',m_.group(1)))
        elif m_.group(2): dep=H.unescape(re.sub('<[^>]+>','',m_.group(2)))
        elif m_.group(3): ep=H.unescape(re.sub('<[^>]+>','',m_.group(3)))
        elif m_.group(4) and sec.startswith('II.') and 'Nombramientos' in sec or (m_.group(4) and re.search(r'II\. Autoridades',sec) and not re.search(r'B\.|Oposiciones',sec)):
            idm=re.search(r'(BOE-A-\d{4}-\d+)',m_.group(5))
            if idm: out.append({'id':idm.group(1),'dep':dep,'ep':ep,'t':H.unescape(re.sub('<[^>]+>','',m_.group(4))).strip(),'u':f'https://www.boe.es/diario_boe/txt.php?id={idm.group(1)}'})
    return out,sorted({x for x in re.findall(r'<h3[^>]*>(.*?)</h3>',t)})
if __name__=='__main__':
    for day in sys.argv[1:]:
        out,secs=fetch_day(day)
        print(day,len(out),secs)
        os.makedirs(f'raw/{day[:4]}',exist_ok=True); json.dump(out,open(f'raw/{day[:4]}/{day}.json','w'),ensure_ascii=False)
