import re,sys
sys.path.insert(0,'/home/user/work/and'); sys.path.insert(0,'/home/user/work/and3')
from ttxt import blocks,assign
D0='/home/user/work/and3/'
PROV=['ALMERÍA','CÁDIZ','CÓRDOBA','GRANADA','HUELVA','JAÉN','MÁLAGA','SEVILLA']
PN={'ALMERÍA':'Almería','CÁDIZ':'Cádiz','CÓRDOBA':'Córdoba','GRANADA':'Granada','HUELVA':'Huelva','JAÉN':'Jaén','MÁLAGA':'Málaga','SEVILLA':'Sevilla'}
SEATS={'2004':dict(zip(PN.values(),[11,15,13,13,11,12,16,18])),'2008':dict(zip(PN.values(),[12,15,12,13,11,12,16,18]))}
FILES={'2004':('ef7520cd-2004_02_17_candidatos_ANDALUCIA.txt','a742e167-2004_03_30_candidatos_electos_ANDALUCIA.txt'),
       '2008':('054c6c66-2008_02_12_candidatos_ANDALUCIA.txt','5f157835-2008_04_01_candidatos_electos_ANDALUCIA.txt')}
# 2004: táboas en imaxe (BOJA núm. 62, 30/03/2004), transcritas. Orde: electores, votantes, a candidaturas, brancos, válidos, nulos
GEN04=[[427305,306943,301477,3583,305060,1883],[927325,647504,634588,8884,643472,4032],[633139,496519,486437,6677,493114,3405],[694333,525010,514434,7035,521469,3541],
 [378492,276563,271286,3318,274604,1959],[525974,422389,414782,4338,419120,3269],[1033539,741002,724934,11326,736260,4742],[1431905,1102615,1078783,17290,1096073,6542],[6052012,4518545,4426721,62451,4489172,29373]]
SEAT04=[[6,140730,5,127998,0,11739,0,13330],[8,307749,5,205625,1,42459,1,46810],[7,226246,4,151857,1,55474,1,31619],[7,255465,5,184691,1,36949,0,22541],
 [7,145170,3,78997,0,20103,1,22010],[7,222596,4,135825,1,27884,0,23943],[8,349404,6,254571,1,55624,1,49017],[11,613185,5,287210,1,86798,1,67404],[61,2260545,37,1426774,6,337030,5,276674]]
T1_04=[[3477,1332,0,317,268,630,322],[5194,19925,1044,1088,800,555,1737],[16051,2105,533,546,550,931,0],[7785,4560,0,696,503,384,860],
 [1712,1669,342,260,265,171,402],[1900,1592,0,383,352,307,0],[5977,4599,1605,1087,877,600,0],[11192,6437,1541,1293,929,859,0],[53288,42219,5065,5670,4544,4437,3321]]
T2_04=[[0,0,1334,0,0],[895,707,0,0,0],[0,0,0,525,0],[0,0,0,0,0],[0,185,0,0,0],[0,0,0,0,0],[1050,0,0,0,523],[1185,750,0,0,0],[3130,1642,1334,525,523]]
COLS={'2004':[['PSOE-A','PP','IULV-CA','PA'],['FA','PSA','NIVA','PH','AA','FE DE LAS JONS','PTPRE'],['IR','PSDA','A-IZ','OTRADEM','UN']],
      '2008':[['PSOE-A','PP','IULV-CA'],['CA','UPYD','VERDES','PDEAL','CANDA','CS','IR'],['PH','PCPA','SAIN','FE DE LAS JONS','PSDA','PFYV','PPCR']]}
SGOUT={'UPYD':'UPyD','FE DE LAS JONS':'FE de las JONS','SAIN':'SAIn','PFYV':'PFyV','CS':'Cs','PDEAL':'PdeAL','CANDA':'CAnda','PPCR':'PPCr'}
def key_of(tit):
    t=re.sub(r'\s+',' ',tit).strip(); m=re.search(r'\(([^()]*)\)\s*$',t); ab=(m.group(1) if m else t).strip().upper()
    k=ab.replace('.','').replace(' ','').replace('’',"'").replace('´',"'")
    M={'PSOEA':'PSOE-A','PSOEDEANDALUCIA':'PSOE-A','IU,LV-CA':'IULV-CA','A':'AA','PS-DA':'PSDA','FEDELASJONS':'FE DE LAS JONS','FE-JONS':'FE DE LAS JONS','FEJONS':'FE DE LAS JONS',"C'S":'CS'}
    return M.get(k,k)
def ca_of(tit):
    t=re.sub(r'\s+',' ',tit).strip(); return re.sub(r'\s*\(([^()]*)\)\s*$','',t).upper()
def results(y):
    V={};S={}
    if y=='2004':
        tot={P:GEN04[i] for i,P in enumerate(PROV+['TOTAL'])}
        for i,P in enumerate(PROV+['TOTAL']):
            for j,g in enumerate(COLS[y][0]): S[(P,g)]=SEAT04[i][2*j]; V[(P,g)]=SEAT04[i][2*j+1]
            for T,cols in ((T1_04,COLS[y][1]),(T2_04,COLS[y][2])):
                for j,g in enumerate(cols): V[(P,g)]=T[i][j]; S[(P,g)]=0
    else:
        B=[assign(b) for b in blocks(D0+FILES[y][1])]; tot=B[0]
        for P in PROV+['TOTAL']:
            for j,g in enumerate(COLS[y][0]): S[(P,g)]=B[1][P][2*j]; V[(P,g)]=B[1][P][2*j+1]
            for bi,cols in enumerate(COLS[y][1:]):
                for j,g in enumerate(cols): V[(P,g)]=B[2+bi][P][j]; S[(P,g)]=0
    # orde común: electores, votantes, válidos, a candidaturas, brancos, nulos
    tot={P:[t[0],t[1],t[4],t[2],t[3],t[5]] for P,t in tot.items()}
    return tot,V,S
if __name__=='__main__':
    import collections
    from pc import parse as p08
    from pc04 import parse as p04
    for y in FILES:
        tot,V,S=results(y); gs=sorted({k[1] for k in V})
        for g in gs:
            s=sum(V[(P,g)] for P in PROV)
            if s!=V[('TOTAL',g)]: print(y,'COLSUM',g,s,V[('TOTAL',g)])
        C=(p04 if y=='2004' else p08)(D0+FILES[y][0]); have=collections.defaultdict(set)
        for c in C:
            if not c.get('np'): have[PN[[k for k,v in PN.items() if v==c['pr']][0]]].add(key_of(c['tit']))
        for P in PROV:
            pv=PN[P]; s=sum(V[(P,g)] for g in gs)
            print(y,pv,'suma',s,'cand',tot[P][3],'OK' if s==tot[P][3] else 'DIF',tot[P][3]-s,'esc',sum(S[(P,g)] for g in gs),SEATS[y][pv], 'v+b',tot[P][3]+tot[P][4]==tot[P][2],'vot',tot[P][2]+tot[P][5]==tot[P][1])
            wv={g for g in gs if V[(P,g)]>0}
            if wv!=have[pv]: print('   só votos',wv-have[pv],' só lista',have[pv]-wv)
        T=tot['TOTAL']; print(y,'TOT', [sum(tot[P][i] for P in PROV)==T[i] for i in range(6)])
