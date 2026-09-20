from pathlib import Path

folders = [
    "app",
    "logs",
]

files = [
    "app/__init__.py",
    "app/ingestion.py",
    "app/retrieval.py",
    "app/order_tool.py",
    "app/agent.py",
    "app/session.py",
    "app/logger.py",
    "main.py",
    ".env.example",
    "requirements.txt",
]

for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

for file in files:
    Path(file).touch(exist_ok=True)

print("Project structure created!")