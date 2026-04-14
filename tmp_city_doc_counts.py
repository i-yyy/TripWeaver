from pathlib import Path
from collections import Counter,defaultdict
root = Path(r'c:\Users\25977\Desktop\hello-agents-main\code\chapter13\helloagents-trip-planner\backend\data\knowledge_base\China')
per_city = Counter()
for p in root.rglob('*.md'):
    if p.name.lower()=='readme.md' or p.name.startswith('_'):
        continue
    city = p.parent.name
    per_city[city]+=1
print('docs', sum(per_city.values()))
print('cities', len(per_city))
for k,v in per_city.most_common(40):
    print(f'{v}\t{k}')
