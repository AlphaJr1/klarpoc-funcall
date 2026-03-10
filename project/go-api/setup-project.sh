#!/bin/bash

# Stop jika ada error
set -e

echo "🚀 Membuat project klar-api..."

# 3. Buat struktur folder internal
mkdir -p cmd/api
mkdir -p internal/domain
mkdir -p internal/usecase
mkdir -p internal/repository/loyverse_api
mkdir -p internal/repository/clickup_api
mkdir -p internal/delivery/http
mkdir -p pkg

# 4. Buat file-file kosong (Placeholder)
touch cmd/api/main.go
touch internal/domain/loyverse.go
touch internal/domain/clickup.go
touch internal/domain/integration.go
touch internal/usecase/sync_usecase.go
touch internal/repository/loyverse_api/loyverse_client.go
touch internal/repository/clickup_api/clickup_client.go
touch internal/delivery/http/handler.go
touch .env

# 5. Tampilkan pesan sukses
echo "✅ Struktur folder Klar-Backend berhasil dibuat!"
echo ""
echo "📂 Struktur project:"
ls -R