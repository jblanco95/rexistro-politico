import re,sys
PROV=['ALMERÍA','CÁDIZ','CÓRDOBA','GRANADA','HUELVA','JAÉN','MÁLAGA','SEVILLA']
def blocks(path):
    L=open(path,encoding='utf8').read().split('\n')
    out=[];cur={}
    for ln in L:
        m=re.match(r'^\s*(ALMERÍA|CÁDIZ|CÓRDOBA|GRANADA|HUELVA|JAÉN|MÁLAGA|SEVILLA|TOTAL|total)\b(.*)$',ln)
        if not m: continue
        lab=m.group(1).upper(); rest=ln
        toks=[(mm.end(),mm.group(0)) for mm in re.finditer(r'(?<![\w.])(\d{1,3}(?:\.\d{3})*|-{3,4})(?![\w.])',ln[m.end(1):])]
        off=m.end(1)
        toks=[(e+off,0 if t.startswith('-') else int(t.replace('.',''))) for e,t in toks]
        cur[lab]=toks
        if lab=='TOTAL': out.append(cur); cur={}
    return out
def assign(b):
    anchors=[e for e,_ in b['TOTAL']]
    res={}
    for lab in PROV+['TOTAL']:
        row=[None]*len(anchors)
        for e,v in b.get(lab,[]):
            i=min(range(len(anchors)),key=lambda i:abs(anchors[i]-e))
            if abs(anchors[i]-e)>6 or row[i] is not None: print('WARN',lab,e,v,anchors,file=sys.stderr)
            row[i]=v
        res[lab]=[x or 0 for x in row]
    # check
    for i in range(len(anchors)):
        s=sum(res[p][i] for p in PROV)
        if s!=res['TOTAL'][i]: print('SUM MISMATCH col',i,s,res['TOTAL'][i],file=sys.stderr)
    return res
if __name__=='__main__':
    for b in blocks(sys.argv[1]):
        r=assign(b)
        for k,v in r.items(): print(k,v)
        print()
