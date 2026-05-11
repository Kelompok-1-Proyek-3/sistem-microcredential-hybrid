# DOKUMEN BRIEF TEKNIS
## Pengembangan Sistem Microcredential Hybrid
*Integrated Microcredential & Professional Certification (IMPC)*

---

| | |
|---|---|
| **Platform ERP** | Odoo 19.0 (Community atau Enterprise) |
| **Versi Dokumen** | 2.0 — Revisi Faktual |
| **Entitas** | Unit Bisnis / Pusat Pelatihan Kampus |
| **Tujuan Sistem** | Mengelola pelatihan hybrid (online & offline) untuk peserta umum (B2C) dan korporat (B2B) secara otomatis dan terintegrasi. |

> **Catatan revisi:** Dokumen ini merevisi draft sebelumnya berdasarkan dokumentasi resmi Odoo 19.0 (odoo.com/documentation/19.0). Poin-poin yang dikoreksi ditandai secara eksplisit.

---

## 1. Arsitektur Modul Odoo 19

Modul-modul berikut harus diinstal dan dikonfigurasi. Nama tampilan mengacu pada Apps menu di Odoo; technical name (addon) dicantumkan sebagai referensi developer.

| Kategori | Nama Modul (UI) | Technical Name | Fungsi Utama |
|---|---|---|---|
| Learning & Certification | eLearning | `website_slides` | Portal materi online (LMS), kuis, sertifikasi. Fitur Certifications diaktifkan dari eLearning → Configuration → Settings. |
| Offline Class | Events | `event` | Manajemen pelatihan tatap muka: tiket, absensi (check-in), dan lokasi. |
| Sales B2C | Website / eCommerce | `website_sale` | Toko online kursus dengan pembayaran otomatis. |
| Sales B2B | Sales | `sale_management` | Quotation, kontrak, dan invoicing paket bundling ke perusahaan. |
| Finance | Accounting | `account` | Invoicing, rekonsiliasi bank, laporan keuangan, dan konfigurasi pajak PPN. |
| Relationship | CRM & Contacts | `crm, contacts` | Database peserta umum (res.partner), instansi, dan pipeline korporat. |
| Operational | Employees | `hr, hr_skills` | Data instruktur/staf internal dan manajemen skill level. HANYA untuk employee, bukan peserta umum. |

> **Koreksi dari draft sebelumnya:** Modul 'Survey' (survey) TIDAK dicantumkan sebagai modul Assessment mandiri. Di Odoo 19, sertifikasi dikelola sepenuhnya dari dalam modul eLearning. Modul survey terinstall otomatis sebagai dependensi teknis, namun bukan modul yang perlu dikonfigurasi secara terpisah oleh pengguna.

---

## 2. Alur Kerja Sistem (Workflow)

### A. Jalur Umum — B2C (Full Online / Self-Service)

1. **Pendaftaran:** User membeli kursus di Website eCommerce (website_sale).
2. **Payment:** Payment gateway (third-party module, lihat Seksi 3) memvalidasi pembayaran.
3. **Enrolment:** User otomatis terdaftar di kursus eLearning setelah pembayaran dikonfirmasi (Enroll Policy: On Payment).
4. **Learning:** User menyelesaikan materi sesuai urutan. Progress dilacak di eLearning → Attendees.
5. **Exam:** User mengerjakan ujian sertifikasi yang dikonfigurasi di eLearning → Configuration → Settings → Certifications (engine berbasis Survey, dikelola dari menu eLearning).
6. **Certification:** Lulus → Sertifikat PDF terbit otomatis dan dikirim via email. User juga mendapat badge di profil portal.

### B. Jalur Korporat / Bundling — B2B (Hybrid)

1. **Kontrak:** Sales team membuat Sales Order (sale_management) untuk paket bundling (mis. 50 pax offline + online).
2. **Invoicing:** Admin mengirimkan invoice termin melalui modul Sales → Invoice.
3. **Akses Peserta:** Admin men-generate Coupon Codes di eLearning ATAU menambahkan email peserta secara massal ke Event yang bersangkutan.
4. **Sesi Offline:** Peserta hadir secara fisik. Panitia melakukan check-in via Odoo Mobile App di modul Events (fitur tersedia di Community maupun Enterprise).
5. **Online Assessment:** Peserta login ke portal untuk mengerjakan ujian akhir sertifikasi — memvalidasi kompetensi secara digital.

---

## 3. Spesifikasi Teknis (Requirements IT)

### 3.1 Sertifikasi & Verifikasi

#### Konfigurasi Certifications di eLearning

- Aktifkan: eLearning → Configuration → Settings → centang Certifications.
- Buat ujian dari eLearning → Courses → [pilih kursus] → tab Certification.
- Konfigurasi: time limit, passing score, randomisasi soal (per-ujian), dan jumlah percobaan.
- Sertifikat PDF terbit otomatis dan dikirim via email saat peserta lulus.

> **Koreksi penting:** Draft sebelumnya menyebut URL `/verify/certificate/<id>` sebagai fitur native Odoo. Ini TIDAK ADA di Odoo 19 secara default. Halaman verifikasi QR code mengarah ke profil peserta di portal. Jika dibutuhkan halaman verifikasi publik standalone, ini merupakan custom development yang harus dianggarkan secara terpisah.

#### Skill Level untuk Instruktur / Staf Internal

- Fitur Skill Management tersedia di Employees → [pilih employee] → tab Resume → Skills.
- Konfigurasi tipe skill dari Employees → Configuration → Skill Types.
- **PENTING:** Fitur ini HANYA berlaku untuk employee (hr.employee), bukan peserta umum di Contacts (res.partner).
- Untuk peserta umum: gunakan Tags di Contacts atau buat custom field via Studio (Enterprise) sebagai pengganti rating kompetensi.

#### Konversi SKS / RPL

- Tambahkan custom field 'Bobot SKS' pada form kursus eLearning sebagai penanda internal.
- **CATATAN PENTING:** Integrasi RPL ke sistem akademik resmi (SISTER/PDDikti) TIDAK dapat dilakukan hanya dengan satu custom field. Diperlukan custom development dan mapping data sesuai format Dikti. Ini harus dianggarkan sebagai scope terpisah.

### 3.2 Integrasi Keuangan

#### Payment Gateway (Midtrans / Xendit)

- Odoo 19 TIDAK menyertakan Midtrans atau Xendit sebagai payment provider native.
- Diperlukan: instalasi modul third-party dari Odoo Apps Store (berbayar) atau pengembangan custom connector.
- Alternatif: Midtrans dan Xendit menyediakan plugin Odoo resmi — pastikan kompatibel dengan versi 19 sebelum instalasi.
- Metode pembayaran yang didukung (setelah modul terpasang): Virtual Account, QRIS, Alfamart/Indomaret.

#### Auto-Tax PPN 11%

- Aktifkan Indonesian Localization dari Accounting → Configuration → Settings → Fiscal Localization.
- Konfigurasi PPN 11% sebagai default tax di Accounting → Configuration → Taxes.
- Set tax default pada produk kursus agar otomatis muncul di setiap invoice.

### 3.3 Dashboard & Reporting

Buat Dashboard (Pivot/Graph View) untuk Direktur Unit yang menampilkan:

- **Revenue:** Pendapatan per kategori kursus (dari Accounting → Reports atau Sales → Dashboard).
- **Success Rate:** Persentase kelulusan peserta per batch (dari eLearning → Reporting → Courses).
- **B2B Performance:** Perusahaan dengan volume peserta terbanyak (dari CRM → Reporting atau Sales).

> **Catatan:** Dashboard custom dapat dibuat menggunakan fitur Spreadsheet (Odoo Enterprise) atau modul Reporting bawaan. Untuk Community edition, gunakan Pivot View dan filter yang sudah tersedia.

---

## 4. Struktur Hak Akses User (Role-Based)

Konfigurasi Groups dan Access Rights di Settings → Users & Companies → Groups:

| Role | Modul yang Dapat Diakses | Keterangan |
|---|---|---|
| Super Admin | Semua modul | Akses penuh. Hanya 1-2 akun. |
| Content Creator | eLearning (Officer) | Upload materi, buat kuis, kelola konten kursus. |
| Finance Officer | Accounting, Sales (read) | Verifikasi pembayaran, kelola invoice dan pajak. |
| Event Coordinator | Events (Manager) | Manajemen absensi offline, check-in peserta, logistik. |
| Instructor / Dosen | eLearning (read), Forum | Akses terbatas: lihat progres peserta, jawab forum diskusi. TIDAK bisa edit materi. |
| Peserta Umum | Portal (website) | Dikelola sebagai Portal User (res.partner), bukan Employee. Akses hanya ke kursus yang dibeli. |

---

## 5. Standar Implementasi & Best Practice

### 5.1 Versi & Lisensi

- Gunakan Odoo 19.0 (rilis September 2025).
- **Community Edition:** gratis, cocok untuk fitur eLearning, Events, Sales, dan Accounting dasar.
- **Enterprise Edition:** diperlukan jika membutuhkan fitur Sign (e-signature kontrak B2B), Spreadsheet (dashboard advanced), atau IoT Box (untuk hardware check-in).
- Odoo Mobile App tersedia untuk KEDUA edisi — bukan eksklusif Enterprise.

### 5.2 Data & Privasi

- Peserta umum WAJIB disimpan sebagai Portal User (res.partner / Contacts), bukan sebagai Employee.
- Alasan utama: efisiensi lisensi (lisensi Odoo dihitung per internal user) dan pemisahan data.
- Hak akses peserta ke modul internal dikontrol via Groups — tidak perlu menjadikan mereka Employee.

### 5.3 Otomasi

- Konfigurasi Automated Actions di Settings → Technical → Automation untuk trigger enrollment, pengiriman email notifikasi, dan status pembayaran.
- Manfaatkan eLearning Paid Courses (aktifkan dari eLearning Settings) agar enrollment terhubung langsung ke eCommerce checkout.
- Target: zero manual intervention dari pembelian kursus hingga sertifikat terbit — fully automated via Odoo workflow.

---

## 6. Catatan Implementasi untuk Tim IT

| Prioritas | Item | Keterangan |
|---|---|---|
| P0 — Wajib | Install modul inti | eLearning, Events, Sales, Accounting, Contacts, Website |
| P0 — Wajib | Enable Certifications | eLearning → Settings → Certifications |
| P0 — Wajib | Enable Paid Courses | eLearning → Settings → Paid Courses (auto-install eCommerce) |
| P0 — Wajib | Konfigurasi PPN 11% | Accounting → Configuration → Taxes + Indonesian Localization |
| P1 — Penting | Payment Gateway | Beli/install modul Midtrans atau Xendit dari Odoo Apps (cek kompatibilitas v19) |
| P1 — Penting | Konfigurasi Role | Buat Groups sesuai Seksi 4 |
| P2 — Opsional | Custom field SKS | Tambahkan via Settings → Technical → Custom Fields atau Odoo Studio |
| P2 — Opsional | Halaman verifikasi sertifikat publik | CUSTOM DEVELOPMENT — tidak tersedia native di Odoo 19. Estimasi scope terpisah. |
| P2 — Opsional | Integrasi RPL ke PDDikti/SISTER | CUSTOM DEVELOPMENT — tidak bisa dilakukan hanya dengan custom field. |

---

## 7. Referensi Dokumentasi

- Odoo 19 eLearning: odoo.com/documentation/19.0/applications/websites/elearning.html
- Odoo 19 Employees & Skills: odoo.com/documentation/19.0/applications/hr/employees.html
- Odoo 19 Events: odoo.com/documentation/19.0/applications/marketing/events.html
- Odoo 19 Accounting (Taxes): odoo.com/documentation/19.0/applications/finance/accounting/taxes.html
- Odoo Apps Store (third-party modules): apps.odoo.com

---

*Dokumen ini disusun berdasarkan dokumentasi resmi Odoo 19.0. Verifikasi ulang setiap modul third-party sebelum instalasi di lingkungan produksi.*
