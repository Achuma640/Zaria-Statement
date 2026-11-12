"""Update the Plot Statement Lookup workbook from the published statement data (index.html).
Needs the PREVIOUS workbook (it holds phones and names, so it is NOT stored in this public repo).
Adds payments/receipts, coverage, comments and contacts; keeps formatting. Data comes from `const D` in index.html,
so run refresh_statement.py first.
"""
from openpyxl import load_workbook
import json,re,datetime,copy
import sys,os
if len(sys.argv)<3: sys.exit('usage: python3 tools/update_lookup_xlsx.py PREVIOUS.xlsx OUT.xlsx  (run from the repo root)')
f,OUT=sys.argv[1],sys.argv[2]
w=load_workbook(f)
s=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','index.html')).read();k=s.index('const D=')+8
D,_=json.JSONDecoder().raw_decode(s[k:])
# Payments
p=w['Payments']
oldK={}
for i in range(2,1001):
    r=p.cell(i,2).value
    if r:oldK[(r,p.cell(i,3).value,p.cell(i,8).value)]=p.cell(i,11).value
rows=sorted(D['P'],key=lambda r:(r[0],r[8],r[1]))
for j,r in enumerate(rows):
    i=2+j;d=datetime.datetime.strptime(r[0]+' '+r[8],'%Y-%m-%d %H:%M')
    vals=[d,r[1],r[2],r[3],r[4],r[5] or None,None,r[7]]
    for c,v in enumerate(vals,1):p.cell(i,c).value=v
    p.cell(i,11).value=oldK.get((r[1],r[2],r[7]),(r[5].split('-')[0] if r[5] else None))
    if i>548:
        for c in (1,2,3,4,5,6,7,8,11):p.cell(i,c)._style=copy.copy(p.cell(548-1,c)._style)
print('payments rows',len(rows),'last row',1+len(rows))
# Plot map for 159-160
pm0=w['Plot map']
for i in range(2,351):
    if str(pm0.cell(i,1).value) in('159','160'):pm0.cell(i,2).value='159-160'
c0=w['Coverage']
for row in c0.iter_rows(min_row=2):
    if row[0].value=='159':row[0].value='159-160'
    elif row[0].value=='160':row[0].value='160 (see 159-160)'
# Coverage
c=w['Coverage'];miss=[];T=lambda b:'=TRUE()' if b else '=FALSE()'
for row in c.iter_rows(min_row=2):
    key=row[0].value
    if key not in D['V']:miss.append(key);continue
    v=D['V'][key]
    for m in range(18):row[1+m].value=T(v['cov'][m])
    row[20].value=v['credit']
    for m in range(14):row[21+m].value=v['rec'][m]
    row[35].value=T(v['master'])
    for m in range(18):row[36+m].value=v['disp'][m] if v['disp'][m]>0 else None
    for m in range(14):row[54+m].value=v['ahead'][m] if v['ahead'][m]>0 else None
print('coverage missing',miss)
# Comments
cm=w['Comments'];have={str(cm.cell(i,5).value) for i in range(2,400) if cm.cell(i,5).value}
last=max(i for i in range(2,400) if cm.cell(i,1).value);add=0
for u,mo,tx in D['N']:
    if tx in have:continue
    last+=1;add+=1
    cm.cell(last,1).value=u;cm.cell(last,2).value=D['U'].get(u,[''])[0] or None;cm.cell(last,3).value=mo;cm.cell(last,4).value='Lump sum spread over months';cm.cell(last,5).value=tx;cm.cell(last,6).value='Y'
    cm.cell(last,7).value=cm.cell(last-1,7).value.replace(str(last-1),str(last)) if isinstance(cm.cell(last-1,7).value,str) else None
    for cc in range(1,8):cm.cell(last,cc)._style=copy.copy(cm.cell(last-1,cc)._style)
print('comments added',add)
# Contacts
ct=w['Contacts'];pm=w['Plot map']
pmap={str(pm.cell(i,1).value):str(pm.cell(i,2).value) for i in range(2,351) if pm.cell(i,1).value}
for i in range(2,401):
    if str(ct.cell(i,2).value) in('159','160'):ct.cell(i,2).value='159-160';pmap={str(pm.cell(i,1).value):str(pm.cell(i,2).value) for i in range(2,351) if pm.cell(i,1).value}
ch=0
for i in range(2,401):
    u=ct.cell(i,2).value
    if u is None:continue
    key=pmap.get(str(u),str(u));n,st=D['U'].get(key,['',''])
    if st and ct.cell(i,4).value!=st:ct.cell(i,4).value=st;ch+=1
    if n and not ct.cell(i,3).value:ct.cell(i,3).value=n;ch+=1
print('contact fields changed',ch)
dig=lambda x:re.sub(r'\D','',str(x))[-9:]
oldk={dig(ct.cell(i,1).value) for i in range(2,601) if ct.cell(i,1).value}
lastc=max(i for i in range(2,601) if ct.cell(i,2).value);addc=0
for ph,u in D['C']:
    if dig(ph) in oldk:continue
    lastc+=1;addc+=1
    ct.cell(lastc,1).value=('0'+ph) if not ph.startswith(('0','+')) else ph;ct.cell(lastc,2).value=u;ct.cell(lastc,3).value=D['U'].get(u,[''])[0] or None;ct.cell(lastc,4).value=D['U'].get(u,['',''])[1] or None
    oldk.add(dig(ph))
print('contacts added',addc)
# Statement footer and treasurer note
st=w['Statement'];_last=max(p[0] for p in D['P']);_d=datetime.datetime.strptime(_last,'%Y-%m-%d');_new='%d %s %d'%(_d.day,_d.strftime('%b'),_d.year)
st['B77'].value=re.sub(r'(– )\d{1,2} \w{3} 20\d\d',lambda m:m.group(1)+_new,st['B77'].value,count=1)
tr=w['Treasurer - How to use']
units={ct.cell(i,2).value for i in range(2,601) if ct.cell(i,1).value}
for r in range(1,13):
    v=tr.cell(r,1).value
    if isinstance(v,str) and 'plots/units currently have a phone number' in v:
        tr.cell(r,1).value=re.sub(r'\d+ of \d+ plots/units','%d of 329 plots/units'%len({pmap.get(str(u),str(u)) for u in units}),v)
w.save(OUT)
print(st['B77'].value[:120])
