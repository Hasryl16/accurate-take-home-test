import os
import pytesseract
import pdfplumber

# Minimum karakter OCR yang dianggap substansial (bukan noise/whitespace belaka).
# Diset >10 agar header pendek dan caption tabel tetap tertangkap.
_OCR_MIN_CHARS = 10

# dpi — cukup untuk OCR akurat tanpa overhead memori berlebihan
_IMAGE_RESOLUTION = 150


def extract_page_text(page, page_img) -> str:
    """Gabungkan teks dari PDF layer dan OCR gambar halaman."""
    pdf_text = page.extract_text() or ""
    ocr_text = pytesseract.image_to_string(page_img, lang="ind+eng")

    # Hanya tambahkan OCR kalau punya konten substansial (>_OCR_MIN_CHARS karakter non-whitespace)
    if len(ocr_text.strip()) > _OCR_MIN_CHARS:
        return (pdf_text + "\n" + ocr_text).strip()
    return pdf_text.strip()


def extract_pages(pdf_path: str) -> list[dict]:
    """
    Ekstrak teks dari semua halaman PDF.
    Return: list of {page_number, text, source_file}
    """
    results = []
    source_file = os.path.basename(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            img = page.to_image(resolution=_IMAGE_RESOLUTION).original
            text = extract_page_text(page, img)
            if text.strip():
                results.append({
                    "page_number": i,
                    "text": text,
                    "source_file": source_file,
                })
            print(f"  Page {i}/{total}: {len(text)} chars extracted")

    return results
