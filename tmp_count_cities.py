from pathlib import Path
root = Path(r'c:\Users\25977\Desktop\hello-agents-main\code\chapter13\helloagents-trip-planner\backend\data\knowledge_base\China')
cities = []
for province in root.iterdir():
    if not province.is_dir():
        continue
    for city in province.iterdir():
        if city.is_dir():
            cities.append(city.name)
print(len(cities))
for name in sorted(cities):
    print(name)
