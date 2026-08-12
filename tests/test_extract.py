from unittest.mock import MagicMock, patch


def test_extract_page_text_combines_pdf_and_ocr():
    """Teks dari PDF layer dan OCR harus digabung."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Teks dari layer PDF."
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="Teks dari OCR screenshot."):
        from extract import extract_page_text
        result = extract_page_text(mock_page, mock_img)

    assert "Teks dari layer PDF." in result
    assert "Teks dari OCR screenshot." in result


def test_extract_page_text_skips_ocr_if_empty():
    """Kalau OCR tidak menemukan teks substansial (<= 50 chars), jangan tambahkan."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Teks PDF saja."
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="   "):
        from extract import extract_page_text
        result = extract_page_text(mock_page, mock_img)

    assert result == "Teks PDF saja."


def test_extract_page_text_handles_none_pdf_text():
    """pdfplumber bisa return None kalau halaman hanya gambar."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_img = MagicMock()

    with patch("extract.pytesseract.image_to_string", return_value="Teks dari screenshot saja."):
        from extract import extract_page_text
        result = extract_page_text(mock_page, mock_img)

    assert "Teks dari screenshot saja." in result
