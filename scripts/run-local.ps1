$env:ENV_FILE = ".env"
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000 --reload
