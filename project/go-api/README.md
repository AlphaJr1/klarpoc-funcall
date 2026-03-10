# Klar API Integrator 

Klar API Integrator adalah layanan backend berbasis Go yang menghubungkan data dari platform **Loyverse** (point-of-sale) dan **ClickUp** (task management). API ini memudahkan pengambilan data ringkasan penjualan, analitik produk terlaris, serta pengelolaan tugas di ClickUp dalam satu antarmuka yang seragam.

---

## 📋 Fitur Utama

- **Loyverse Integration**:
  - Ambil ringkasan harian (Revenue, Transaksi, Barang Terjual).
  - Analitik produk terlaris berdasarkan tanggal tertentu dengan limiter.
  - Metrik performa berdasarkan rentang tanggal (Date Range).
  - Kelola data Toko, Barang, Resi, dan Karyawan (dengan dukungan cursor).
- **ClickUp Integration**:
  - Pembuatan tugas (Task Creation).
  - Update detail tugas (Nama, Deskripsi, Status, Due Date).
  - Pengambilan detail tugas secara real-time.
- **Auto Documentation**: Swagger UI otomatis untuk mempermudah testing.

---

## Prasyarat (Prerequisites)

Sebelum menjalankan project, pastikan Anda telah menginstal:
- [Go](https://golang.org/dl/) (Versi 1.20 ke atas)
- [Swag CLI](https://github.com/swaggo/swag) (Untuk generate dokumentasi API)

---

##  Cara Menjalankan Server

### 1. Konfigurasi Environment (`.env`)
Buat file `.env` di direktori root project dan isi data berikut:
```env
PORT=8080
LOYVERSE_API_KEY=your_loyverse_token_here
LOYVERSE_BASE_URL=https://api.loyverse.com/v1.0
CLICKUP_API_KEY=your_clickup_token_here
CLICKUP_BASE_URL=https://api.clickup.com/api/v2
```

### 2. Install Dependencies
Buka terminal dan jalankan:
```bash
go mod tidy
```

### 3. Generate Dokumentasi Swagger
Setiap kali ada perubahan pada anotasi API (di file `handler.go`), jalankan perintah ini:
```bash
swag init -g cmd/api/main.go --output docs --parseDependency --parseInternal
```

### 4. Jalankan Server
Jalankan aplikasi Go:
```bash
go run cmd/api/main.go
```
Server akan berjalan di `http://localhost:8080` (atau port sesuai `.env`).

---

## 📖 Akses Dokumentasi Swagger

Setelah server berjalan, Anda dapat mengakses dokumentasi interaktif (UI) di:
👉 **[http://localhost:8080/swagger/index.html](http://localhost:8080/swagger/index.html)**

Di sini Anda bisa mencoba langsung seluruh endpoint (Try it out) tanpa perlu Postman.

---

## 📡 Daftar Endpoint Utama

### Loyverse
| Nama | Method | Endpoint | Note |
|------|--------|----------|------|
| Daily Summary | GET | `/api/v1/loyverse/summary` | Filter: `store_id`, `date` |
| Top Products | GET | `/api/v1/loyverse/top-products` | Filter: `store_id`, `date`, `limit` |
| Metrics Range | GET | `/api/v1/loyverse/metrics` | Filter: `start_date`, `end_date` |
| List Employees | GET | `/api/v1/loyverse/employees` | Dukungan cursor pagination |

### ClickUp
| Nama | Method | Endpoint | Note |
|------|--------|----------|------|
| Create Task | POST | `/api/v1/clickup/list/{list_id}/task` | Create new task |
| Update Task | PUT | `/api/v1/clickup/tasks/{task_id}` | Update Name, Desc, Status, Due Date |
| Task Details | GET | `/api/v1/clickup/tasks/{task_id}` | Fetch task metadata |

---

##  Troubleshooting (Pesan Error Umum)

**1. Port Already in Use (8080)**
Jika muncul error `bind: address already in use`, matikan proses yang sedang berjalan:
```bash
lsof -i :8080
kill -9 [PID_YANG_MUNCUL]
```

**2. Token Invalid (Status 500)**
Pastikan API Key di `.env` sudah menyertakan prefix (jika diperlukan) atau sudah benar sesuai dashboard Loyverse/ClickUp.

---

**Developed by Al*

