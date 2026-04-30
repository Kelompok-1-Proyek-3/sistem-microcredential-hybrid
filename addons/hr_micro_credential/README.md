# HR Microcredential - Odoo Custom Addon

Custom module untuk **HR Group** pada platform Microcredential IMPC.

## Fitur

- **Learning Progress Dashboard** - Real-time monitoring progress belajar karyawan
- **Hybrid Attendance Tracking** - Monitoring status check-in untuk course hybrid
- **At-Risk Detection** - Deteksi otomatis karyawan yang tertinggal
- **Skills Mapping** - Otomatis update skill dari sertifikat course
- **Learning Analytics** - Dashboard analytics per departemen
- **Employee Learning Profile** - Tab tambahan pada form karyawan

## Dependencies

- `hr` (Odoo native)
- `hr_skills` (Odoo native)
- `mail` (Odoo native)

## Instalasi

1. Tambahkan path `sistem-microcredential-hybrid/addons` ke `--addons-path` di konfigurasi Odoo
2. Update App List di Odoo
3. Install module "HR Microcredential"

## Struktur

```
hr_micro_credential/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── hr_micro_credential_api.py     # API endpoint untuk Website Group
├── data/
│   ├── ir_cron_data.xml               # Scheduled actions (sync + analytics)
│   ├── mail_template_data.xml         # Email template at-risk alert
│   └── hr_micro_credential_demo.xml   # Demo data
├── models/
│   ├── __init__.py
│   ├── hr_learning_progress.py        # Sync cache dari eLearning
│   ├── hr_learning_profile_note.py    # Private HR notes
│   ├── hr_learning_analytics.py       # Daily analytics snapshot
│   ├── hr_course_skill_mapping.py     # Course → Skill mapping
│   ├── hr_skill_mapping_log.py        # Audit log perubahan skill
│   └── hr_employee.py                 # Extend hr.employee
├── security/
│   ├── hr_micro_credential_security.xml  # Groups & record rules
│   └── ir.model.access.csv              # Model access rights
├── static/
│   └── src/scss/
│       └── hr_micro_credential.scss   # Custom styles
└── views/
    ├── hr_learning_progress_views.xml     # Dashboard views
    ├── hr_learning_profile_note_views.xml # Notes views
    ├── hr_learning_analytics_views.xml    # Analytics views
    ├── hr_course_skill_mapping_views.xml  # Skill mapping config
    ├── hr_skill_mapping_log_views.xml     # Audit log views
    ├── hr_employee_views.xml              # Employee form extension
    └── hr_micro_credential_menus.xml      # Menu structure
```
