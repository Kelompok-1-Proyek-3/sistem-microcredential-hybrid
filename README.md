# IMPC - Indonesia Microcredential Platform Center

Platform LMS berbasis **Odoo 19** untuk microcredential dengan dukungan pembelajaran hybrid (online + offline), enrollment B2C/B2B, sertifikasi digital, dan integrasi HR.

## Arsitektur

```
sistem-microcredential-hybrid/
├── addons/
│   ├── impc_website/          # Portal website, eLearning, sertifikat digital
│   ├── impc_lms/              # Core LMS: learner, enrollment, sertifikat
│   ├── impc_hr_skills_sync/   # Sinkronisasi skill karyawan dari course
│   ├── sale_microcredential/  # Manajemen kontrak & redeem code B2B
│   └── marketing_microcredential/  # Report & survey marketing
├── config/
│   ├── odoo.conf              # Konfigurasi Odoo (jangan di-commit)
│   └── odoo.conf.example      # Template konfigurasi
├── docs/                      # Dokumentasi PRD & analisis
└── docker-compose.yml         # Deployment Odoo + PostgreSQL
```

## Modul Kustom

| Modul | Fungsi Utama |
|-------|-------------|
| **impc_website** | Portal publik & student, katalog course, enrollment, sertifikat digital dengan QR code, verifikasi publik |
| **impc_lms** | Core data model: learner, enrollment, competency, offline session, eticket, certificate base |
| **impc_hr_skills_sync** | Sinkronisasi skill employee dari completion course, dashboard learning analytics, at-risk notification |
| **sale_microcredential** | Kontrak B2B, portal HR partner, generate redeem code, invoice & email automation |
| **marketing_microcredential** | Survey satisfaction & NPS, event conversion tracking, report marketing |

## Fitur Utama

- **Hybrid Learning** — Course online/offline/hybrid dengan exam gating berbasis absensi
- **B2C Enrollment** — Pembelian course via eCommerce + payment gateway
- **B2B Contract** — Kontrak perusahaan, redeem code untuk karyawan
- **Digital Certificate** — Sertifikat dengan QR code + hash verifikasi publik
- **HR Sync** — Sinkronisasi skill & learning progress ke employee record
- **Marketing Automation** — Survey post-course, NPS, automation based on event

## Persyaratan

- Docker & Docker Compose
- Odoo 19.0 (image: `odoo:latest`)
- PostgreSQL 14

## Instalasi & Setup

```bash
# 1. Clone repository
git clone <repo-url> && cd sistem-microcredential-hybrid

# 2. Setup konfigurasi
cp config/odoo.conf.example config/odoo.conf
# Edit config/odoo.conf — isi admin_passwd

# 3. Jalankan container
docker compose up -d

# 4. Akses Odoo
# http://localhost:8069
# Buat database baru, instal modul yang diinginkan
```

## Branch Strategy

| Branch | Deskripsi |
|--------|-----------|
| `deployment` | Branch utama siap deploy |
| `main` | Base bersama, sinkron dari deployment |
| `hr_group` | Pengembangan modul HR |
| `sales_group` | Pengembangan modul sales |
| `marketing_group` | Pengembangan modul marketing |
| `website` | Pengembangan portal website |
| `fix-hr-odoo19` | Fix & patch untuk kompatibilitas Odoo 19 |

## Pengembangan

Urutan merge yang direkomendasikan:

```
feature/module branch → deployment (via PR/test branch)
```

Sebelum push ke `deployment`, buat `test-merge-deployment` untuk validasi konflik.

## Teknologi

- **Odoo 19.0** (Community Edition)
- **Python 3.12** — Backend logic
- **PostgreSQL 14** — Database
- **Docker** — Containerization
- **Chart.js** — Learning analytics dashboard
- **qrcode** — QR code generation (opsional)
