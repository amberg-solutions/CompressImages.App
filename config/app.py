import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
FILE_DIR = os.path.join(BASE_DIR, "files")

if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR, exist_ok=True)