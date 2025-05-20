from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

QUEUE_FILE = BASE_DIR / "queue.json"
if not QUEUE_FILE.exists():
    QUEUE_FILE.write_text("[]")