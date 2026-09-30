import os
from PIL import Image, ImageEnhance
import pytesseract

# Auto-configure tesseract path if installed on Windows
for path in [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe'),
]:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break


class TextExtractor:
    @staticmethod
    def extract_text_from_image(image_path: str) -> str:
        # 1. Try grayscale + contrast enhancement for maximum OCR readability
        try:
            image = Image.open(image_path)
            gray = image.convert("L")
            contrast_boost = ImageEnhance.Contrast(gray).enhance(2.0)
            text = pytesseract.image_to_string(contrast_boost)
            if text and len(text.strip()) > 3:
                return text.strip()
        except Exception:
            pass

        # 2. Fallback to raw original image
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception:
            return ""
