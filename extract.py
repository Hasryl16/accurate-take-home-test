import os
import pytesseract
import pdfplumber


def extract_page_text(page, page_img) -> str:
    """Gabungkan teks dari PDF layer dan OCR gambar halaman."""
    pdf_text = page.extract_text() or ""
    ocr_text = pytesseract.image_to_string(page_img, lang="ind+eng")

    # Hanya tambahkan OCR kalau punya konten substansial (>10 karakter non-whitespace)
    if len(ocr_text.strip()) > 10:
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
            img = page.to_image(resolution=150).original
            text = extract_page_text(page, img)
            if text.strip():
                results.append({
                    "page_number": i,
                    "text": text,
                    "source_file": source_file,
                })
            print(f"  Page {i}/{total}: {len(text)} chars extracted")

    return results
