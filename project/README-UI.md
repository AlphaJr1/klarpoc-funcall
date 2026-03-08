# UI Visualisasi State Machine Router AI

Project ini telah ditambahkan antarmuka (UI) Next.js modern menggunakan `assistant-ui` untuk memvisualisasikan cara kerja Agentic AI secara real-time. UI terbagi menjadi 3 panel: Task Queue, Agent Processing (berbasis thread streaming mock/real), dan Task Detail.

## Persyaratan

- Python 3.9+ (Untuk menjalankan backend FastAPI)
- Node.js 18+ (Untuk menjalankan frontend Next.js)

## Cara Menjalankan Project (Local Development)

### 1. Jalankan Backend Server (FastAPI)

Buka terminal baru, pastikan Anda berada di virtual environment yang sama dengan project Python sebelumnya, lalu install dependencies FastAPI:

```bash
cd project
pip install fastapi uvicorn
```

Jalankan server:

```bash
python api.py
```

_Server akan berjalan di http://localhost:8000_

### 2. Jalankan Frontend Server (Next.js)

Buka terminal lainnya dan jalankan aplikasi Next.js:

```bash
cd project/ui
npm run dev
```

_Aplikasi web akan berjalan di http://localhost:3000_

## Fitur UI

1. **Task Queue (Kiri)**: Menampilkan list task (open) dari `clickup.json`. Badge prioritas otomatis diberi warna sesuai tingkatannya.
2. **Agent Processing (Tengah)**: Memanfaatkan primitive thread dari `assistant-ui` untuk memvisualisasikan SSE (Server-Sent Events). Anda bisa melihat tahap state detection, tool calling, tool result, confidence score, dan final response secara live dan berurutan!
3. **Task Detail (Kanan)**: Apabila proses selesai, panel ini akan menampilkan detail dari task (status resolusi, feedback comment/reasoning bot, dan peringatan eskalasi apabila confidence rendah).

> **Catatan Mock vs Real API:**  
> Jika Anda langsung menjalankan frontend tanpa API, aplikasi akan otomatis menggunakan koneksi Mock Streaming yang telah disediakan. Untuk visualisasi terbaik dan konektivitas live, jalankan kedua server (Backend dan Frontend).
