from pathlib import Path
root = Path(r'c:\Users\25977\Desktop\hello-agents-main\code\chapter13\helloagents-trip-planner\backend\data\knowledge_base\China')
docs = [p for p in root.rglob('*.md') if p.name.lower() != 'readme.md' and not p.name.startswith('_')]
print(len(docs))
