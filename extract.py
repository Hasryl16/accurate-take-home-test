import os
import pytesseract
import pdfplumber


_OCR_MIN_CHARS = 10

_IMAGE_RESOLUTION = 150


def extract_page_text(page, page_img) -> str:
    pdf_text = page.extract_text() or ""
    ocr_text = pytesseract.image_to_string(page_img, lang="ind+eng")

    if len(ocr_text.strip()) > _OCR_MIN_CHARS:
        return (pdf_text + "\n" + ocr_text).strip()
    return pdf_text.strip()


def extract_pages(pdf_path: str) -> list[dict]:
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
