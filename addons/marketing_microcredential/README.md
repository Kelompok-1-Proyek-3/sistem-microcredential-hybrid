# Marketing Microcredential - Odoo Custom Addon

Custom module untuk **Marketing Group** pada platform Microcredential IMPC.

## Fitur

- **Weekly Event Conversion** - Laporan konversi event mingguan (registered, attended, enrolled)
- **Monthly Survey Report** - Laporan bulanan survey (response count, average score, NPS)
- **CSV Export Automation** - Export CSV otomatis via scheduled actions
- **Event to Course Linking** - Link event ke course (slide.channel) untuk analitik konversi

## Dependencies

- `event` (Odoo native)
- `website_event` (Odoo native)
- `survey` (Odoo native)
- `website_slides` (Odoo native)
- `utm` (Odoo native)

## Instalasi

1. Tambahkan path `sistem-microcredential-hybrid/addons` ke `--addons-path` di konfigurasi Odoo
2. Update App List di Odoo
3. Install module "Marketing Microcredential"

## Catatan Implementasi

- QR scan check-in tetap native di Events + Odoo Mobile App (tanpa custom code)
- Data konversi event mengacu pada event yang di-link ke course via slide.channel.event_id
- NPS dihitung berdasarkan pertanyaan yang dipilih di survey (field nps_question_id)

