import re,sys,collections
sys.path.insert(0,'/home/user/work/and')
from ttxt import blocks,assign,PROV
from pc import parse
PN={'ALMERÍA':'Almería','CÁDIZ':'Cádiz','CÓRDOBA':'Córdoba','GRANADA':'Granada','HUELVA':'Huelva','JAÉN':'Jaén','MÁLAGA':'Málaga','SEVILLA':'Sevilla'}
SEATS={'Almería':12,'Cádiz':15,'Córdoba':12,'Granada':13,'Huelva':11,'Jaén':11,'Málaga':17,'Sevilla':18}
D0='/home/user/work/and2/'
FILES={'2012':('056fd0cf-2012_02_28_candidatos_ANDALUCIA.txt','3eae9546-2012_04_17_candidatos_electos_ANDALUCIA.txt'),
       '2015':('090f40cb-2015_02_24_candidatos_ANDALUCIA.txt','dd87f467-2015_04_15_candidatos_electos_ANDALUCIA.txt')}
COLS={'2012':[['PP','PSOE-A','IULV-CA'],
   ['UPYD','PA','EQUO','PACMA','EB','HARTOS.ORG','PCPE','ECNP','FE DE LAS JONS','PUM+J','FC'],
   ['CDL','PRAO','SAIN','UCE','PH','PHAN','SYR','CONVERGENCIA ANDALUZA','AES','CCD'],
   ['MSR','MD','PFYV','AMD','PDSA','AUPAL','PNDEA','CREA','RISA']],
 '2015':[['PSOE-A','PP','PODEMOS','CS','IULV-CA'],
   ['UPYD','PA','PACMA','VOX','CILUS','FE DE LAS JONS','RECORTES CERO','PCPE','PUM+J','EB'],
   ['PBG','PTJ','SYR','LYG','PNDEA','NEODEMÓCRATAS','PRAO','RISA','CÁMBIALO']]}
SGOUT={'UPYD':'UPyD','HARTOS.ORG':'HARTOS.org','FE DE LAS JONS':'FE de las JONS','SAIN':'SAIn','SYR':'SyR','PFYV':'PFyV','PNDEA':'PNdeA','CREA':'C.Re.A.','CS':'Cs','CÁMBIALO':'CÁMBIALO'}
def key_of(tit):
    t=re.sub(r'\s+',' ',tit).strip(); m=re.search(r'\(([^()]*)\)\s*$',t); ab=(m.group(1) if m else t).strip().upper()
    ab=ab.replace("C'S",'CS').replace('E.C.N.P.','ECNP').replace('U.C.E.','UCE').replace('P.N.DE A.','PNDEA').replace('PN DE A','PNDEA').replace('C.RE.A.','CREA')
    if 'RECORTES CERO' in ab: return 'RECORTES CERO'
    if ab.startswith('HARTOS'): return 'HARTOS.ORG'
    if ab=='EQUO ANDALUCÍA': return 'EQUO'
    return ab
def ca_of(tit):
    t=re.sub(r'\s+',' ',tit).strip(); return re.sub(r'\s*\(([^()]*)\)\s*$','',t).upper()
def results(y):
    B=[assign(b) for b in blocks(D0+FILES[y][1])]
    tot=B[0]; V={}; S={}
    for j,g in enumerate(COLS[y][0]):
        for P in PROV: S[(P,g)]=B[1][P][2*j]; V[(P,g)]=B[1][P][2*j+1]
    for bi,cols in enumerate(COLS[y][1:]):
        b=B[2+bi]; assert len(b['TOTAL'])==len(cols)
        for j,g in enumerate(cols):
            for P in PROV: V[(P,g)]=b[P][j]; S[(P,g)]=0
    gs=sorted({k[1] for k in V})
    for g in gs: V[('TOTAL',g)]=sum(V[(P,g)] for P in PROV); S[('TOTAL',g)]=sum(S[(P,g)] for P in PROV)
    return tot,V,S
if __name__=='__main__':
    for y in FILES:
        tot,V,S=results(y); C=parse(D0+FILES[y][0]); gs=sorted({k[1] for k in V})
        have=collections.defaultdict(set)
        for c in C:
            if not c.get('np'): have[c['pr']].add(key_of(c['tit']))
        for P in PROV:
            pv=PN[P]; s=sum(V[(P,g)] for g in gs)
            print(y,pv,'suma',s,'cand',tot[P][3],'OK' if s==tot[P][3] else 'DIF %d'%(tot[P][3]-s),'esc',sum(S[(P,g)] for g in gs),SEATS[pv])
            wv={g for g in gs if V[(P,g)]>0}
            if wv!=have[pv]: print('   só votos',wv-have[pv],' só lista',have[pv]-wv)
        print(y,'TOTAL', sum(V[('TOTAL',g)] for g in gs), tot['TOTAL'][3])
