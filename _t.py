import glob,os,re
fs=sorted(glob.glob('content/posts/*.md'))[-15:]
for f in fs:
    t=open(f,encoding='utf-8').read()
    m=re.search(r'title:\s*"?([^"\n]+)',t)
    print(os.path.basename(f),'::',m.group(1) if m else '?')
