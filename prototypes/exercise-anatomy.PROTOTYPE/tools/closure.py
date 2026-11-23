import re,sys,glob,os
d=os.path.expanduser('~/Documents/curricula/godot')
pre={};title={}
for f in glob.glob(d+'/GD-*.*.*-*.md'):
    t=open(f).read()
    h=t.splitlines()[0][2:]; i=h.split()[0]; title[i]=h
    m=re.search(r'^## Prereqs\n(.*?)^## ',t,re.S|re.M)
    pre[i]=re.findall(r'^- \[?(GD-\d+\.\d+\.\d+)',m.group(1),re.M)
for root in sys.argv[1:]:
    seen=[];st=list(pre[root])
    while st:
        x=st.pop()
        if x in seen: continue
        seen.append(x); st+=pre[x]
    print(f'== {title[root]}  ({len(seen)})')
    for x in sorted(seen): print('  ',title[x])
