# Alur Ingestion — Penjelasan Step-by-Step

## Gambaran Besar

```
PDF (34MB, 64 halaman)
    │
    ▼  Step 1: Ekstraksi
    │  extract.py
    │
    ▼  Step 2: Chunking  
    │  chunker.py
    │
    ▼  Step 3: Embedding
    │  ingestion.py → Cohere API
    │
    ▼  Step 4: Penyimpanan
       qdrant_store.py → Qdrant
```

Total waktu untuk 64 halaman: ~3–5 menit (dominan: OCR + Cohere API calls).

---

## Step 1: Ekstraksi PDF (`extract.py`)

### Mengapa Dua Sumber?

PDF menyimpan konten dalam dua bentuk:

1. **Text layer** — teks yang bisa di-copy-paste. `pdfplumber` membacanya langsung.
2. **Gambar/screenshot** — teks yang "terjebak" dalam gambar. Perlu OCR untuk dibaca.

Modul Accurate Online penuh dengan tangkapan layar tampilan software. Banyak informasi 
penting (nama field, instruksi langkah) hanya ada di dalam gambar, bukan text layer.

### Proses per Halaman

```python
# Untuk setiap halaman:
pdf_text = page.extract_text()          # dari text layer (pdfplumber)
img = page.to_image(resolution=150)     # render halaman jadi gambar
ocr_text = pytesseract.image_to_string(img, lang="ind+eng")  # OCR

# Gabungkan jika OCR punya konten substansial (>10 karakter)
if len(ocr_text.strip()) > 10:
    combined = pdf_text + "\n" + ocr_text
```

### Mengapa `lang="ind+eng"`?

Modul berbahasa Indonesia tapi istilah teknis (Purchase Order, Invoice, Vendor) 
berbahasa Inggris. Kombinasi `ind+eng` membuat Tesseract lebih akurat untuk teks campuran.

### Mengapa `resolution=150`?

150 DPI adalah titik optimal antara akurasi OCR dan kecepatan/memori:
- Di bawah 100 DPI: karakter kecil sulit dikenali
- Di atas 200 DPI: akurasi naik sedikit tapi memori gambar meledak
- 150 DPI: cukup untuk mengenali teks ukuran 10–12pt di screenshot

---

## Step 2: Chunking (`chunker.py`)

Lihat `docs/chunking-strategy.md` untuk penjelasan mendalam.

Intinya: setiap halaman diproses secara independen, sehingga `page_number` selalu 
akurat sebagai metadata setiap chunk.

Output setiap chunk:
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  # UUID unik
    "page_number": 15,                              # untuk sitasi
    "chunk_index": 2,                               # urutan dalam halaman
    "source_file": "MODUL PEMBELAJARAN.pdf",
    "text": "...isi chunk..."
}
```

---

## Step 3: Embedding (`ingestion.py → embed_chunks`)

### Apa itu Embedding?

Embedding adalah representasi numerik teks sebagai vektor (array angka). Teks 
dengan makna serupa menghasilkan vektor yang "dekat" secara matematis.

```
"Faktur Pembelian"    → [0.12, -0.34, 0.89, ...] (1024 angka)
"Purchase Invoice"    → [0.11, -0.33, 0.91, ...] (sangat dekat!)
"Resep Nasi Goreng"   → [-0.55, 0.22, -0.14, ...] (jauh)
```

Inilah yang membuat pencarian semantik bekerja — bukan mencari kata yang sama, 
tapi makna yang sama.

### Mengapa Cohere embed-multilingual-v3.0?

Model ini dilatih pada teks dari 100+ bahasa termasuk Bahasa Indonesia. Alternatifnya 
`embed-english-v3.0` hanya optimal untuk Bahasa Inggris — retrieval untuk pertanyaan 
berbahasa Indonesia akan kurang akurat.

Output: vektor 1024 dimensi per chunk (float32).

### Batching

Cohere API membatasi 96 teks per request. Dengan 170 chunks, kita kirim dalam 2 batch:
- Batch 1: chunks 0–89 (90 teks)
- Batch 2: chunks 90–169 (80 teks)

---

## Step 4: Penyimpanan ke Qdrant (`qdrant_store.py`)

### Apa itu Qdrant?

Qdrant adalah **vector database** — database yang dioptimalkan untuk menyimpan 
dan mencari vektor secara efisien.

Konsep utama:
- **Collection** — seperti "tabel", kumpulan points dengan dimensi vektor yang sama
- **Point** — satu entri: `id` (UUID) + `vector` (1024 float) + `payload` (JSON metadata)
- **Cosine similarity** — cara mengukur kemiripan vektor (0–1, makin tinggi = lebih mirip)

### Idempotency: Mengapa Delete Sebelum Upsert?

Jika script dijalankan dua kali tanpa delete terlebih dahulu, setiap chunk akan 
tersimpan duplikat — retrieval akan mengembalikan hasil dobel dan menurunkan kualitas 
jawaban.

Solusi: sebelum ingest, hapus semua points dengan `source_file == "MODUL PEMBELAJARAN.pdf"`:

```python
client.delete(collection_name=collection, points_selector=Filter(
    must=[FieldCondition(key="source_file", match=MatchValue(value="MODUL PEMBELAJARAN.pdf"))]
))
```

Lalu upsert dari nol. Script bisa dijalankan berulang kali dengan aman.

### Cara Kerja Retrieval (saat chatbot menjawab)

Saat pengguna bertanya:
1. Pertanyaan di-embed menjadi vektor dengan `input_type="search_query"`
2. Qdrant mencari `top-k` vektor yang paling dekat (cosine similarity)
3. Mengembalikan payload: `{text, page_number, source_file}`
4. `text` dimasukkan sebagai konteks ke LLM
5. `page_number` digunakan chatbot untuk menyebut sumber

### Socket Patch: Mengapa Ada `qdrant_socket_patch.py`?

Qdrant instance berada di belakang Cloudflare (CDN/WAF). Cloudflare secara default 
melayani koneksi IPv6, tapi koneksi langsung ke port 6333 (Qdrant native) hanya 
mendukung IPv4.

`qdrant_socket_patch.py` meng-intercept `socket.getaddrinfo` dan memaksa koneksi 
menggunakan IP langsung (`QDRANT_DIRECT_IP`) sehingga bypass Cloudflare routing.

---

## Ringkasan Angka

| Metrik | Nilai |
|---|---|
| Halaman PDF | 64 |
| Halaman dengan konten | 64 |
| Total chunks | 170 |
| Dimensi embedding | 1024 |
| Waktu ingestion | ~3–5 menit |
| Qdrant points | 170 |
