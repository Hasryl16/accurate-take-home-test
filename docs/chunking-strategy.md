# Strategi Chunking — Penjelasan Lengkap

## Apa itu Chunking dan Kenapa Perlu?

Model embedding seperti Cohere hanya bisa memproses teks hingga sekitar 512 token 
(~2.000 karakter) sekaligus. Dokumen 64 halaman tidak bisa langsung di-embed seluruhnya.

Selain itu, retrieval lebih akurat dengan chunk yang terfokus. Menemukan 1 paragraf 
yang relevan jauh lebih mudah daripada mencari di seluruh halaman sekaligus — analoginya 
seperti mencari buku di perpustakaan vs. mencari halaman di buku yang sudah ditemukan.

---

## 3 Pendekatan yang Dipertimbangkan

### Opsi 1 — Word-based Flat Chunking

```
[Seluruh teks dokumen] → potong per 500 kata → chunk-chunk
```

**Kelebihan:** Simple, tidak bergantung pada struktur dokumen.  
**Kekurangan:** Kehilangan info halaman. Kita tidak tahu chunk berasal dari halaman 
berapa — padahal setiap jawaban wajib menyertakan nomor halaman (persyaratan W2).

---

### Opsi 2 — Page-aware Chunking ✓ **(yang digunakan)**

```
Halaman 1 → chunk 1a (page=1), chunk 1b (page=1)
Halaman 2 → chunk 2a (page=2)
Halaman 3 → chunk 3a (page=3), chunk 3b (page=3)
```

**Kelebihan:** Nomor halaman tersimpan akurat di setiap chunk sebagai metadata.  
**Kekurangan:** Halaman yang teksnya sangat panjang tetap perlu dipecah lebih lanjut.

---

### Opsi 3 — Section-based Chunking

```
"Bab 1: Persiapan Accurate Online" → chunk per bab
"Fitur Pembelian" → chunk per sub-bagian
```

**Kelebihan:** Paling koheren secara semantik.  
**Kekurangan:** Bergantung pada deteksi header. Jika header berbentuk gambar/screenshot 
(banyak terjadi di modul ini), deteksi akan gagal.

---

## Parameter yang Digunakan

```python
RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " ", ""],
    chunk_size=800,
    chunk_overlap=100,
)
```

### `chunk_size=800` — Mengapa 800 Karakter?

- Batas Cohere embed-multilingual: ~512 token ≈ ~1.500 karakter
- 800 karakter memberikan ruang aman (53% dari batas)
- Rata-rata 1 paragraf modul = 200–600 karakter → 800 bisa menampung 1–3 paragraf
- Cukup konteks untuk menjawab pertanyaan spesifik

### `chunk_overlap=100` — Mengapa Overlap?

Tanpa overlap, kalimat penting bisa terpotong di ujung chunk dan "hilang" dari keduanya:

```
Chunk A: "...Faktur Pembelian adalah dokumen yang digunakan untuk mencatat transaksi 
          pembelian barang atau jasa dari pemasok. Dokumen ini"
Chunk B: "berisi informasi seperti nama pemasok, tanggal, jumlah barang..."
```

Dengan overlap 100 karakter, akhir Chunk A muncul kembali di awal Chunk B, memastikan 
kalimat "Dokumen ini berisi..." tidak terputus konteksnya.

### `separators=["\n\n", "\n", ".", " ", ""]` — Urutan Prioritas

RecursiveCharacterTextSplitter mencoba separator dari kiri ke kanan. Ia lebih suka 
memotong di `\n\n` (paragraf) daripada `\n` (baris), baris daripada kalimat (`.`), 
kalimat daripada kata (` `). `""` adalah fallback terakhir: potong karakter demi 
karakter (jarang terjadi).

---

## Contoh Konkret: Halaman 15 (2.996 karakter)

```
Halaman 15 (2.996 chars) — di atas chunk_size 800

Split menjadi:
├── Chunk 0 (800 chars): "Persiapan Data Pemasok\n\nData pemasok adalah..." 
│   metadata: {page_number: 15, chunk_index: 0}
├── Chunk 1 (800 chars): "...nama pemasok, alamat, NPWP, dan informasi..." 
│   metadata: {page_number: 15, chunk_index: 1}
├── Chunk 2 (800 chars): "...kontak yang akan digunakan saat membuat..."
│   metadata: {page_number: 15, chunk_index: 2}
└── Chunk 3 (596 chars): "...Faktur Pembelian. Pastikan data sudah benar."
    metadata: {page_number: 15, chunk_index: 3}
```

Saat user bertanya soal data pemasok dan retrieval menemukan Chunk 2, chatbot 
tahu jawabannya berasal dari **Halaman 15** dan bisa menyebutnya sebagai sumber.

---

## Hasil Aktual

Setelah ingestion modul 64 halaman:
- Total chunks: **170**
- Rata-rata per halaman: ~2,7 chunks
- Halaman terpendek: 1 chunk (halaman berisi sedikit teks)
- Halaman terpanjang: ~5 chunks (halaman padat teks + OCR)
