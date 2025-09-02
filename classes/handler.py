from PIL import Image as PILImage
from config import FILE_DIR
import os

class Handler:

    @classmethod
    def compress_img(cls, imgFile, uid: str, quality: int, format: str = "JPEG") -> tuple[int, int] | None:
        if not imgFile:
            return None

        imgFile.stream.seek(0, os.SEEK_END)
        kbBefore = int(imgFile.stream.tell() / 1024)
        imgFile.stream.seek(0)

        image = PILImage.open(imgFile.stream)

        if format == "JPEG" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        ext = format.lower()
        compPath = os.path.join(FILE_DIR, f"{uid}.{ext}")

        save_kwargs = {"optimize": True}
        if format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality

        image.save(compPath, format, **save_kwargs)

        kbAfter = int(os.path.getsize(compPath) / 1024)
        return kbBefore, kbAfter

    @staticmethod
    def get_img_bytes(uid: str, format: str) -> bytes | None:
        ext = format.lower()
        fPath = os.path.join(FILE_DIR, f"{uid}.{ext}")
        if os.path.exists(fPath):
            with open(fPath, "rb") as f:
                data = f.read()
            try:
                os.remove(fPath)
            except Exception as e:
                print(f"Could not delete {fPath}: {e}")
            return data
        return None
    
    @staticmethod
    def read_img_file(uid: str, format: str) -> bytes | None:
        fPath = os.path.join(FILE_DIR, f"{uid}.{format.lower()}")
        if os.path.exists(fPath):
            with open(fPath, "rb") as f:
                return f.read()
        return None
