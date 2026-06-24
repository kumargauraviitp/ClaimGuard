import os
import shutil

STORAGE_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")

DIRECTORIES = [
    "uploads",
    "evidence",
    "reports",
    "exports",
    "knowledge",
    "temp",
    "archives"
]

class StorageManager:
    def __init__(self):
        self.ensure_directories()

    def ensure_directories(self):
        for d in DIRECTORIES:
            path = os.path.join(STORAGE_BASE, d)
            os.makedirs(path, exist_ok=True)

    def get_path(self, category: str, filename: str) -> str:
        if category not in DIRECTORIES:
            raise ValueError(f"Invalid storage category: {category}")
        return os.path.join(STORAGE_BASE, category, filename)

    def save_file(self, category: str, filename: str, content: bytes) -> str:
        path = self.get_path(category, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def delete_file(self, category: str, filename: str):
        path = self.get_path(category, filename)
        if os.path.exists(path):
            os.remove(path)

    def clear_temp(self):
        temp_dir = os.path.join(STORAGE_BASE, "temp")
        for f in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

storage_manager = StorageManager()
