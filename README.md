# Accenture Take-Home Test — RAG Chatbot (Accurate Online)

**Stack:** Python (ingestion) + n8n (chatbot workflow)  
**Deadline:** 17 Agustus 2026

---

## Arsitektur Sistem

```
MODUL PEMBELAJARAN.pdf (64 halaman, 34MB)
            │
            ▼
  [Python Ingestion Pipeline]
  ├── pdfplumber   → ekstrak text layer per halaman
  └── pytesseract  → OCR screenshot & gambar per halaman
            │
            ▼
  RecursiveCharacterTextSplitter
  (per halaman · chunk_size=800 · overlap=100)
  metadata: page_number, source_file, chunk_index
            │
            ▼
  Cohere embed-multilingual-v3.0
  (batch 90 · input_type="search_document")
            │
            ▼
  Qdrant Vector Store
  (collection: accenture · 170 points · cosine similarity)
            │
            ▼
  [n8n Chatbot Workflow]
  ├── Cohere embed query
  ├── Qdrant top-k retrieval
  ├── Window Buffer Memory (10 giliran)
  └── LLM + System Prompt → jawaban + sitasi halaman
```

---

## Cara Menjalankan dari Nol

### 1. System Dependencies

```bash
# Fedora/RHEL
sudo dnf install tesseract tesseract-langpack-ind -y

# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-ind -y

# Verify
tesseract --version
```

### 2. Python Environment

```bash
cd accenture/
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
cp .env.example .env
# Edit .env dan isi semua variabel
```

| Variabel | Keterangan |
|---|---|
| `COHERE_API_KEY` | API key dari dashboard.cohere.com |
| `QDRANT_URL` | URL Qdrant instance (HTTP) |
| `QDRANT_API_KEY` | API key Qdrant |
| `QDRANT_COLLECTION` | Nama collection, default: `accenture` |

### 4. Letakkan PDF

```bash
# Letakkan "MODUL PEMBELAJARAN.pdf" di folder docs/
ls docs/MODUL\ PEMBELAJARAN.pdf
```

### 5. Jalankan Ingestion

```bash
python ingestion.py
```

Output yang diharapkan:
```
========================================
  Accenture RAG — Ingestion Pipeline
========================================
[1/4] Extracting pages ... → 64 halaman
[2/4] Chunking ...         → 170 chunks
[3/4] Generating embeddings ...
[4/4] Upserting ke Qdrant ...
✓ Ingestion selesai!
```

Script **aman dijalankan berulang kali** — data lama dihapus sebelum ingestion baru (idempotent).

### 6. Jalankan Tests

```bash
pytest tests/ -v
# Expected: 14 passed
```

---

## Keputusan Teknis

### Model Embedding: Cohere embed-multilingual-v3.0

`embed-multilingual-v3.0` dilatih untuk 100+ bahasa termasuk Indonesia, memberikan retrieval yang lebih relevan untuk konten akuntansi berbahasa Indonesia.

### Strategi Chunking: Page-aware + RecursiveCharacterTextSplitter

**Chunk size 800 karakter, overlap 100:** Setiap chunk rata-rata 1–2 paragraf — cukup konteks untuk retrieval tanpa mendekati batas token embedding. Overlap 100 karakter (~1 kalimat) mencegah informasi penting terpotong di perbatasan chunk.

**Per halaman (bukan flat):** Dengan memproses setiap halaman secara independen, metadata `page_number` tersimpan akurat di setiap chunk. Chatbot bisa menyebut "Halaman 12" sebagai sumber jawaban

**RecursiveCharacterTextSplitter:** Urutan separator `["\n\n", "\n", ".", " ", ""]` memastikan pemotongan terjadi di batas paragraf/kalimat terlebih dahulu, bukan di tengah kata.

### Ekstraksi PDF: pdfplumber + pytesseract

Modul Accurate Online padat tangkapan layar. `pdfplumber` mengekstrak text layer (teks yang bisa di-copy), sementara `pytesseract` men-OCR setiap halaman sebagai gambar untuk menangkap teks di dalam screenshot. Keduanya digabungkan per halaman; OCR hanya ditambahkan jika menghasilkan ≥10 karakter substansial (mencegah noise whitespace).

### Mekanisme Memori Percakapan (n8n)

Chatbot menggunakan **Window Buffer Memory** dengan 10 giliran terakhir (5 user + 5 assistant). Pendekatan ini dipilih karena:
- Cukup untuk semua skenario uji B (maksimal 4 giliran)
- Tidak memerlukan LLM call tambahan untuk summarization
- Deterministik dan mudah dijelaskan

Riwayat yang memanjang: saat melebihi 10 giliran, giliran paling lama dihapus (sliding window). Untuk konteks percakapan customer support yang biasanya singkat, ini sudah memadai.

### Vector Store: Qdrant

Instance Qdrant sudah tersedia (self-hosted). Collection `accenture` menggunakan cosine similarity — metrik standar untuk semantic search dengan normalized embeddings. Setiap point menyimpan payload `{page_number, chunk_index, source_file, text}` untuk retrieval dan sitasi.

---

## Keterbatasan yang Disadari

| Keterbatasan | Dampak | Rencana Perbaikan |
|---|---|---|
| OCR pytesseract bisa noise | Screenshot resolusi rendah menghasilkan karakter aneh | Post-processing regex; atau gunakan model multimodal (Gemini Vision) |
| Tabel gambar jadi teks linier | Kehilangan struktur baris/kolom | Deteksi tabel dengan pdfplumber + rekonstruksi teks terstruktur |
| Tanpa evaluasi otomatis | Akurasi diukur manual | Implementasi RAGAS dengan set 10–20 Q&A acuan (N1) |
| Window memory sederhana | Percakapan sangat panjang (>10 giliran) kehilangan konteks awal | Summarization memory untuk sesi panjang |
| Satu PDF saja | Tidak ada mekanisme update dokumen parsial | Versioning per dokumen dengan `doc_id` metadata |


## Struktur File

```
accenture/
├── ingestion.py            — orchestrator pipeline utama
├── extract.py              — PDF text extraction + OCR
├── chunker.py              — page-aware chunking
├── qdrant_store.py         — Qdrant client wrapper
├── qdrant_socket_patch.py  — bypass Cloudflare WAF untuk Qdrant
├── tests/
│   ├── test_extract.py     — 4 unit tests
│   ├── test_chunker.py     — 6 unit tests
│   └── test_qdrant_store.py — 4 unit tests
├── docs/
│   ├── MODUL PEMBELAJARAN.pdf
│   ├── chunking-strategy.md
│   └── ingestion-flow.md
├── .env.example
├── requirements.txt
└── README.md
```
