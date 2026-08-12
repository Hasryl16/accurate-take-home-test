from unittest.mock import MagicMock, patch
from extract import extract_page_text


def test_extract_page_text_combines_pdf_and_ocr():
    """Teks dari PDF layer dan OCR harus digabung."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Teks dari layer PDF."
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="Teks dari OCR screenshot."):
        result = extract_page_text(mock_page, mock_img)

    assert "Teks dari layer PDF." in result
    assert "Teks dari OCR screenshot." in result


def test_extract_page_text_skips_ocr_if_empty():
    """Kalau OCR tidak menemukan teks substansial (<= 10 chars), jangan tambahkan."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Teks PDF saja."
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="   "):
        result = extract_page_text(mock_page, mock_img)

    assert result == "Teks PDF saja."


def test_extract_page_text_handles_none_pdf_text():
    """pdfplumber bisa return None kalau halaman hanya gambar."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="Teks dari screenshot saja."):
        result = extract_page_text(mock_page, mock_img)

    assert "Teks dari screenshot saja." in result


def test_extract_page_text_includes_short_but_real_ocr():
    """OCR output dengan 11+ karakter harus dimasukkan (threshold >10)."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF text."
    mock_img = MagicMock()

    # 15 chars — above threshold of >10
    with patch("extract.pytesseract.image_to_string", return_value="OCR 15 chars!!"):
        result = extract_page_text(mock_page, mock_img)

    assert "OCR 15 chars!!" in result
