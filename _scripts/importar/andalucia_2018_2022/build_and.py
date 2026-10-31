import re,sys,json,collections,unicodedata
from parse_cand import parse,splitname
from ttxt import blocks,assign,PROV
PN={'ALMERÍA':'Almería','CÁDIZ':'Cádiz','CÓRDOBA':'Córdoba','GRANADA':'Granada','HUELVA':'Huelva','JAÉN':'Jaén','MÁLAGA':'Málaga','SEVILLA':'Sevilla'}
SEATS={'Almería':12,'Cádiz':15,'Córdoba':12,'Granada':13,'Huelva':11,'Jaén':11,'Málaga':17,'Sevilla':18}
# abreviatura no BOJA (candidaturas) -> sg
def sg_of(year,tit):
    t=re.sub(r'\s+',' ',tit).strip()
    m=re.search(r'\(([^()]*)\)\s*$',t)
    ab=m.group(1).strip() if m else t
    ab=re.sub(r'\s*-\s*','-',ab) if 'RECORTES' in ab or 'ADELANTE' in ab else ab
    if ab.startswith('RECORTES CERO'): return 'RECORTES CERO' if year=='2022' else 'RECORTES CERO-M+J-GV'
    return {'EB':'ESCAÑOS EN BLANCO','P.C.O.E.':'PCOE','N.A.':'NA','Federación BASTA YA!':'BASTA YA!','UNIDOS SÍ-Democracia Efectiva':'UNIDOS SÍ'}.get(ab,ab)
def ca_of(tit):
    t=re.sub(r'\s+',' ',tit).strip()
    t=re.sub(r'\s*\(([^()]*)\)\s*$','',t)
    t=re.sub(r'\s*\(PSOE-A\)$','',t)
    return t
COLS={'2018':[['PSOE-A','PP','Cs','ADELANTE ANDALUCÍA','VOX'],
              ['PACMA','AxSÍ','EQUO-INICIATIVA','RECORTES CERO-M+J-GV','PCPA','UPYD','NA'],
              ['IxH','CILUS','PCOE','ESCAÑOS EN BLANCO','FE de las JONS','ALTER','CAnda'],
              ['RESPETO','CILU-LINARES','IZAR','SOLUCIONA','ConecAnd','UNIDOS SÍ','RISA']],
      '2022':[['PP','PSOE-A','VOX','PorA','ADELANTE ANDALUCÍA-ANDALUCISTAS'],
              ['Cs','PACMA','JM+','AL','ESCAÑOS EN BLANCO','PCPA','PUM+J'],
              ['XH','NA','PCTE','RECORTES CERO','CRSxA','PARTIDO AUTÓNOMOS','FE de las JONS'],
              ['LOS VERDES','JxG','VOLT','JUFUDI','SOMOS FUTURO','DESPIERTA','IZAR','BASTA YA!']]}
FILES={'2018':('955c330b-2018_11_06_candidatos_ANDALUCIA.txt','6492d5bb-2018_12_26_candidatos_electos_ANDALUCIA.txt'),
       '2022':('15d82d56-2022_05_24_candidatos_ANDALUCIA.txt','219dcf89-2022_07_12_candidatos_electos_ANDALUCIA.txt')}
def results(y):
    B=[assign(b) for b in blocks(FILES[y][1])]
    tot=B[0]; V={}; S={}
    seat=B[1]
    off=1 if y=='2022' else 0
    for j,sg in enumerate(COLS[y][0]):
        for P in PROV+['TOTAL']:
            S[(P,sg)]=seat[P][off+2*j]; V[(P,sg)]=seat[P][off+2*j+1]
    for bi,cols in enumerate(COLS[y][1:]):
        b=B[2+bi]; assert len(b['TOTAL'])==len(cols),(y,bi,len(b['TOTAL']))
        for j,sg in enumerate(cols):
            for P in PROV+['TOTAL']: V[(P,sg)]=b[P][j]; S[(P,sg)]=0
    return tot,V,S
if __name__=='__main__':
    for y in ['2018','2022']:
        tot,V,S=results(y)
        C=[c for c in parse(FILES[y][0]) if not c.get('np')]
        have=collections.defaultdict(set)
        for c in C: have[c['pr']].add(sg_of(y,c['tit']))
        sgs=sorted({k[1] for k in V})
        for P in PROV:
            pv=PN[P]; s=sum(V[(P,g)] for g in sgs); vc=tot[P][3]
            print(y,pv,'suma',s,'vc',vc,'OK' if s==vc else 'DIF %d'%(vc-s), 'seats',sum(S[(P,g)] for g in sgs),SEATS[pv])
            withv={g for g in sgs if V[(P,g)]>0}
            if withv!=have[pv]: print('   only votes:',withv-have[pv],' only list:',have[pv]-withv)
