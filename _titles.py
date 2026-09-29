import glob, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
for f in sorted(glob.glob(r'D:\projects\seo_blogs\content\posts\*2026-09*.md')):
    txt = open(f, encoding='utf-8').read()
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', txt, re.M)
    print(os.path.basename(f), '|', m.group(1) if m else '?')
