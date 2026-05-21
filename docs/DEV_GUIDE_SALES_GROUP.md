# Panduan Developer: Sales Group — Modul `sale_microcredential`
**Tim**: Sales Group (3 Developer)  
**Modul Odoo Target**: `sale`, `crm`, `contacts`  
**Modul Custom**: `sale_microcredential`  
**Referensi PRD**: `4. PRD_SALES_GROUP.md`  
**Tanggal**: 2026

---

## DAFTAR ISI

1. [Gambaran Umum & Arsitektur](#1-gambaran-umum--arsitektur)
2. [Struktur File Modul (Lengkap)](#2-struktur-file-modul-lengkap)
3. [Git Workflow & Protokol Koordinasi](#3-git-workflow--protokol-koordinasi)
4. [DEV 1 — Data Foundation (Model & Security)](#4-dev-1--data-foundation-model--security)
5. [DEV 2 — Business Logic & Workflow](#5-dev-2--business-logic--workflow)
6. [DEV 3 — Views, Portal & Report](#6-dev-3--views-portal--report)
7. [Urutan Pengerjaan & Dependency Matrix](#7-urutan-pengerjaan--dependency-matrix)
8. [Testing Checklist (Shared)](#8-testing-checklist-shared)
9. [FAQ & Konvensi Kode](#9-faq--konvensi-kode)

---

## 1. Gambaran Umum & Arsitektur

### Pembagian Tugas Berdasarkan Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    sale_microcredential                         │
├─────────────────┬───────────────────────┬───────────────────────┤
│   DEV 1         │       DEV 2           │       DEV 3           │
│  Data Layer     │   Business Logic      │    Presentation       │
│                 │   & Workflow Layer    │       Layer           │
├─────────────────┼───────────────────────┼───────────────────────┤
│ models/         │ models/ (workflow)    │ views/                │
│ security/       │ services/             │ templates/ (portal)   │
│ __manifest__.py │ wizards/              │ controllers/          │
│                 │ data/ (XML rules)     │ report/               │
└─────────────────┴───────────────────────┴───────────────────────┘
     SELESAI          MULAI setelah          BISA PARALEL
     MINGGU 1         Dev 1 push models     setelah Dev 1 push
```

### Prinsip Anti-Conflict

- **Setiap dev memegang file terpisah** — tidak ada dua dev yang edit file yang sama secara bersamaan.
- **Dev 1** membuat skeleton, fields, dan security. **Dev 2** dan **Dev 3** bisa mulai paralel setelah `models/` di-push Dev 1.
- **Metode workflow** dipisah ke file `sale_order_workflow.py` (Dev 2) agar tidak bentrok dengan `sale_order.py` (Dev 1).
- `__manifest__.py` di-update sesuai **jadwal merge yang sudah ditentukan** (lihat Section 3).

---

## 2. Struktur File Modul (Lengkap)

```
addons/
└── sale_microcredential/
    ├── __init__.py                          ← DEV 1
    ├── __manifest__.py                      ← DEV 1 (buat), lalu DEV 2 & DEV 3 tambahkan entry
    │
    ├── models/
    │   ├── __init__.py                      ← DEV 1
    │   ├── sale_order.py                    ← DEV 1 (fields only, NO methods)
    │   ├── sale_order_line.py               ← DEV 1 (fields only)
    │   ├── sale_order_workflow.py           ← DEV 2 (action methods, compute, onchange)
    │   ├── res_partner.py                   ← DEV 1 (fields only)
    │   └── res_users.py                     ← DEV 1 (is_hr_partner_admin field)
    │
    ├── services/
    │   ├── __init__.py                      ← DEV 2
    │   └── redeem_code_service.py           ← DEV 2
    │
    ├── wizards/
    │   ├── __init__.py                      ← DEV 2
    │   ├── redeem_code_wizard.py            ← DEV 2
    │   └── wizard_views.xml                 ← DEV 2
    │
    ├── controllers/
    │   ├── __init__.py                      ← DEV 3
    │   └── portal_contract.py               ← DEV 3
    │
    ├── views/
    │   ├── sale_order_views.xml             ← DEV 3
    │   ├── res_partner_views.xml            ← DEV 3
    │   └── dashboard_views.xml              ← DEV 3
    │
    ├── templates/
    │   ├── portal_contract_list.xml         ← DEV 3
    │   ├── portal_contract_detail.xml       ← DEV 3
    │   └── portal_redeem_codes.xml          ← DEV 3
    │
    ├── data/
    │   ├── email_templates.xml              ← DEV 2
    │   ├── server_actions.xml               ← DEV 2
    │   └── ir_cron.xml                      ← DEV 2
    │
    ├── report/
    │   ├── sale_contract_report_action.xml  ← DEV 2
    │   └── sale_contract_report_template.xml ← DEV 3
    │
    └── security/
        ├── ir.model.access.csv              ← DEV 1
        └── sale_microcredential_groups.xml  ← DEV 1
```

---

## 3. Git Workflow & Protokol Koordinasi

### Branch Strategy

```
main
└── dev/sales-group           ← Branch utama tim Sales
    ├── dev/sales-dev1-models       ← DEV 1
    ├── dev/sales-dev2-workflow     ← DEV 2
    └── dev/sales-dev3-views        ← DEV 3
```

### Urutan Push yang WAJIB Diikuti

```
[HARI 1-3]   DEV 1 push models + security ke dev/sales-dev1-models
             → Merge ke dev/sales-group
             → DEV 2 & DEV 3 pull & mulai branch masing-masing

[HARI 4-7]   DEV 2 & DEV 3 bekerja PARALEL di branch masing-masing
             → Tidak ada edit file yang sama

[HARI 8]     DEV 2 push → PR ke dev/sales-group
             DEV 3 push → PR ke dev/sales-group
             → Merge satu per satu (DEV 2 dulu, lalu DEV 3)

[HARI 9]     Update __manifest__.py bersama (video call 15 menit)
             → DEV 1 update manifest dari list yang dikumpulkan Dev 2 & Dev 3
```

### Aturan `__manifest__.py`

- **HANYA DEV 1** yang commit ke `__manifest__.py`.
- Dev 2 dan Dev 3 membuat file, lalu **kirim path file ke DEV 1** via chat untuk ditambahkan ke `data` list manifest.
- Ini menghilangkan kemungkinan merge conflict pada manifest.

---

## 4. DEV 1 — Data Foundation (Model & Security)

**Estimasi**: 3 hari  
**Branch**: `dev/sales-dev1-models`  
**Prioritas**: PERTAMA — Dev 2 dan Dev 3 bergantung pada ini

### 4.1 File: `__init__.py` (root)

```python
# addons/sale_microcredential/__init__.py
from . import models
from . import services
from . import wizards
from . import controllers
```

---

### 4.2 File: `__manifest__.py`

> Dev 1 buat skeleton awal. Dev 2 & Dev 3 akan memberikan path file untuk ditambahkan ke bagian `data`.

```python
# addons/sale_microcredential/__manifest__.py
{
    'name': 'Sale Microcredential B2B',
    'version': '19.0.1.0.0',
    'summary': 'B2B Contract Management & HR Partner Portal for Microcredential IMPC',
    'category': 'Sales/Sales',
    'depends': [
        'sale_management',
        'crm',
        'contacts',
        'portal',
        'mail',
        'base_setup',
    ],
    'data': [
        # Security (DEV 1)
        'security/sale_microcredential_groups.xml',
        'security/ir.model.access.csv',

        # Data & Automation (DEV 2) — tambahkan saat merge DEV 2
        # 'data/email_templates.xml',
        # 'data/server_actions.xml',
        # 'data/ir_cron.xml',

        # Wizard Views (DEV 2) — tambahkan saat merge DEV 2
        # 'wizards/wizard_views.xml',

        # Backend Views (DEV 3) — tambahkan saat merge DEV 3
        # 'views/sale_order_views.xml',
        # 'views/res_partner_views.xml',
        # 'views/dashboard_views.xml',

        # Portal Templates (DEV 3) — tambahkan saat merge DEV 3
        # 'templates/portal_contract_list.xml',
        # 'templates/portal_contract_detail.xml',
        # 'templates/portal_redeem_codes.xml',

        # Report (DEV 2 action + DEV 3 template)
        # 'report/sale_contract_report_action.xml',
        # 'report/sale_contract_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
```

---

### 4.3 File: `models/__init__.py`

```python
# addons/sale_microcredential/models/__init__.py
from . import sale_order
from . import sale_order_line
from . import sale_order_workflow   # Dev 2 yang isi, tapi import disini Dev 1 buat
from . import res_partner
from . import res_users             # is_hr_partner_admin field (KOREKSI: bukan di res.partner)
```

> **CATATAN**: Dev 1 buat file `sale_order_workflow.py` kosong (stub) agar import tidak error. Dev 2 yang mengisi isinya.

**Stub file untuk Dev 2** — Dev 1 buat ini:
```python
# addons/sale_microcredential/models/sale_order_workflow.py
# =====================================================
# FILE INI DIKERJAKAN OLEH DEV 2
# Dev 1 hanya membuat stub kosong agar import tidak error
# =====================================================
from odoo import models
```

---

### 4.4 File: `models/sale_order.py`

> **ATURAN**: File ini HANYA boleh berisi field definitions. TIDAK ADA method, TIDAK ADA @api.depends, TIDAK ADA action button. Semua itu ada di `sale_order_workflow.py` (Dev 2).

```python
# addons/sale_microcredential/models/sale_order.py
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ── CONTRACT TYPE ──────────────────────────────────────────
    contract_type = fields.Selection(
        selection=[
            ('B2C', 'B2C - Individual'),
            ('B2B_CONTRACT', 'B2B - Corporate Contract'),
        ],
        string='Contract Type',
        default='B2C',
        required=True,
        tracking=True,
    )
    partner_type = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Corporate HR'),
            ('CORPORATE_OTHER', 'Corporate - Other'),
        ],
        string='Partner Type',
        default='INDIVIDUAL',
        tracking=True,
    )

    # ── CONTRACT PERIOD ────────────────────────────────────────
    contract_start_date = fields.Date(
        string='Contract Start Date',
        tracking=True,
    )
    expiry_date = fields.Date(
        string='Contract Expiry Date',
        tracking=True,
    )
    renewal_opportunity = fields.Boolean(
        string='Flag Renewal',
        default=False,
        help='Otomatis True jika expiry_date < 30 hari dari hari ini.',
    )
    renewed_to_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Renewed To',
        ondelete='set null',
        copy=False,
    )

    # ── REDEEM CODE TRACKING ───────────────────────────────────
    redeem_codes_generated = fields.Boolean(
        string='Redeem Codes Generated',
        default=False,
        copy=False,
    )
    redeem_code_batch_id = fields.Char(
        string='Redeem Code Batch ID',
        copy=False,
    )
    redeem_codes_requested_at = fields.Datetime(
        string='Redeem Requested At',
        copy=False,
    )
    redeem_codes_generated_at = fields.Datetime(
        string='Redeem Generated At',
        copy=False,
    )
    redeem_code_batch_status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('GENERATED', 'Generated'),
            ('FAILED', 'Failed'),
        ],
        string='Batch Status',
        default='PENDING',
        copy=False,
    )
```

---

### 4.5 File: `models/sale_order_line.py`

```python
# addons/sale_microcredential/models/sale_order_line.py
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── COURSE LINKAGE ─────────────────────────────────────────
    # KOREKSI ODOO 19: nama field slide_channel_id (bukan course_id) — sesuai PRD
    # Menggunakan comodel_name='slide.channel' (bukan elearning.course)
    slide_channel_id = fields.Many2one(
        comodel_name='slide.channel',   # model eLearning native di Odoo 19
        string='Course',
        ondelete='set null',
    )
    learning_mode = fields.Selection(
        selection=[
            ('ONLINE', 'Online'),
            ('OFFLINE', 'Offline'),
            ('HYBRID', 'Hybrid'),
        ],
        string='Learning Mode',
        readonly=True,
        help='Diambil read-only dari course (dikelola Website Group).',
    )
    hybrid_session_summary = fields.Text(
        string='Jadwal Sesi Tatap Muka',
        readonly=True,
        help='READ-ONLY. Diisi dari event yang di-link ke course oleh Marketing Group.',
    )

    # ── REDEEM CODE CONFIG PER LINE ────────────────────────────
    redeem_code_count = fields.Integer(
        string='Jumlah Redeem Code',
        default=0,
    )
    redeem_code_expiry_days = fields.Integer(
        string='Masa Berlaku Kode (Hari)',
        default=90,
    )
    student_count = fields.Integer(
        string='Jumlah Peserta',
        default=1,
    )
    course_access_duration_days = fields.Integer(
        string='Durasi Akses Kursus (Hari)',
        default=90,
    )
```

---

### 4.6 File: `models/res_partner.py`

```python
# addons/sale_microcredential/models/res_partner.py
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type_microcredential = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Perusahaan - HR'),
            ('CORPORATE_OTHER', 'Perusahaan - Lainnya'),
        ],
        string='Tipe Partner',
        default='INDIVIDUAL',
    )
    industry_type = fields.Selection(
        selection=[
            ('TECH', 'Teknologi'),
            ('FINANCE', 'Keuangan'),
            ('MANUFACTURING', 'Manufaktur'),
            ('OTHER', 'Lainnya'),
        ],
        string='Industri',
    )
    employee_count = fields.Integer(
        string='Jumlah Karyawan',
    )
    training_budget_annual = fields.Float(
        string='Budget Pelatihan Tahunan (IDR)',
    )
    # KOREKSI ODOO 19: is_hr_partner_admin DIPINDAH ke res.users
    # Field ini TIDAK boleh ada di res.partner — lihat models/res_users.py
    # is_hr_partner_admin ada di res.users karena berkaitan dengan login/portal user,
    # bukan dengan contact record.
```

---

### 4.6b File: `models/res_users.py`

> ⚠️ **KOREKSI ODOO 19**: `is_hr_partner_admin` ditambahkan ke `res.users` (bukan `res.partner`).  
> Portal users = `res.users` dengan group `base.group_portal`. Field ini menandai user portal yang menjadi HR admin B2B.

```python
# addons/sale_microcredential/models/res_users.py
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_hr_partner_admin = fields.Boolean(
        string='HR Portal Admin',
        default=False,
        help=(
            'Tandai user portal sebagai admin HR mitra B2B. '
            'Memberikan akses melihat semua kontrak & redeem code milik perusahaannya. '
            'Untuk membuat portal user: set groups_id = [(4, ref("base.group_portal"))]'
        ),
    )
```

> **Cara membuat portal user HR** (dari Sales Group):
> ```python
> # Membuat portal user untuk HR manager
> portal_group = self.env.ref('base.group_portal')
> user = self.env['res.users'].create({
>     'name': 'HR Manager PT ABC',
>     'login': 'hr.manager@ptabc.co.id',
>     'email': 'hr.manager@ptabc.co.id',
>     'partner_id': partner_id,  # FK ke res.partner
>     'groups_id': [(4, portal_group.id)],
>     'is_hr_partner_admin': True,
> })
> ```

---

### 4.7 File: `security/sale_microcredential_groups.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Group: HR Partner (akses portal) -->
        <record id="group_hr_partner" model="res.groups">
            <field name="name">HR Partner</field>
            <field name="category_id" ref="base.module_category_sales_sales"/>
            <field name="comment">Akses portal untuk HR perusahaan mitra B2B.</field>
        </record>

        <!-- Group: Sales Manager Microcredential -->
        <record id="group_sales_microcredential_manager" model="res.groups">
            <field name="name">Sales Manager Microcredential</field>
            <field name="category_id" ref="base.module_category_sales_sales"/>
            <field name="implied_ids" eval="[(4, ref('sales_team.group_sale_manager'))]"/>
        </record>
    </data>
</odoo>
```

---

### 4.8 File: `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sale_order_microcredential,sale.order microcredential,sale.model_sale_order,sales_team.group_sale_salesman,1,1,1,0
access_sale_order_line_microcredential,sale.order.line microcredential,sale.model_sale_order_line,sales_team.group_sale_salesman,1,1,1,0
access_res_partner_microcredential,res.partner microcredential,base.model_res_partner,sales_team.group_sale_salesman,1,1,1,0
access_res_users_microcredential,res.users microcredential,base.model_res_users,sales_team.group_sale_salesman,1,1,1,0
access_hr_partner_sale_order,hr partner sale.order read,sale.model_sale_order,sale_microcredential.group_hr_partner,1,0,0,0
access_hr_partner_sale_order_line,hr partner sale.order.line read,sale.model_sale_order_line,sale_microcredential.group_hr_partner,1,0,0,0
```

---

### 4.9 Checklist Dev 1

- [ ] Buat folder `addons/sale_microcredential/` beserta semua subfolder
- [ ] Buat semua `__init__.py` di setiap folder
- [ ] Buat `__manifest__.py` (skeleton dengan entry security aktif, entry lain di-comment)
- [ ] Buat `models/sale_order.py` (fields only)
- [ ] Buat `models/sale_order_line.py` (fields only, termasuk `slide_channel_id` FK ke `slide.channel`)
- [ ] Buat `models/res_partner.py` (fields only, tanpa `is_hr_partner_admin`)
- [ ] Buat `models/res_users.py` (fields only, berisi `is_hr_partner_admin`)
- [ ] Buat `models/sale_order_workflow.py` (STUB KOSONG saja — isi oleh Dev 2)
- [ ] Buat `security/sale_microcredential_groups.xml`
- [ ] Buat `security/ir.model.access.csv`
- [ ] **Test**: `docker-compose up` → install modul → pastikan tidak ada error pada instalasi
- [ ] **Push & notify** Dev 2 dan Dev 3 bahwa models sudah siap

---

## 5. DEV 2 — Business Logic & Workflow

**Estimasi**: 4 hari  
**Branch**: `dev/sales-dev2-workflow`  
**Mulai**: Setelah Dev 1 push models (pull dulu dari `dev/sales-group`)  
**File yang BOLEH disentuh**: Hanya file dalam list berikut — JANGAN edit file milik Dev 1 atau Dev 3.

### File Milik Dev 2 (EKSKLUSIF):

```
models/sale_order_workflow.py     ← tulis ulang (Dev 1 buat stub)
services/__init__.py
services/redeem_code_service.py
wizards/__init__.py
wizards/redeem_code_wizard.py
wizards/wizard_views.xml
data/email_templates.xml
data/server_actions.xml
data/ir_cron.xml
report/sale_contract_report_action.xml
```

---

### 5.1 File: `models/sale_order_workflow.py`

> File ini berisi semua **action methods**, **compute fields**, dan **onchange** untuk `sale.order`. DEV 1 sudah membuat stub kosong — Dev 2 mengisinya.

```python
# addons/sale_microcredential/models/sale_order_workflow.py
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderWorkflow(models.Model):
    """
    Extension untuk sale.order — khusus business logic dan workflow.
    Fields didefinisikan di sale_order.py (Dev 1).
    """
    _inherit = 'sale.order'

    # ── COMPUTE: Renewal Flag ──────────────────────────────────
    @api.depends('expiry_date')
    def _compute_renewal_opportunity(self):
        from datetime import date, timedelta
        today = date.today()
        threshold = today + timedelta(days=30)
        for order in self:
            if order.expiry_date and order.expiry_date <= threshold:
                order.renewal_opportunity = True
            else:
                order.renewal_opportunity = False

    # ── ACTION: Generate Redeem Codes ─────────────────────────
    def action_request_redeem_codes(self):
        """
        Buka wizard untuk konfirmasi request redeem code ke Website API.
        Dipanggil dari tombol di form view (Dev 3 yang buat tombolnya di XML).
        """
        self.ensure_one()
        if self.contract_type != 'B2B_CONTRACT':
            raise UserError('Redeem code hanya untuk kontrak tipe B2B.')
        if self.redeem_codes_generated:
            raise UserError('Redeem code untuk kontrak ini sudah pernah di-generate.')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Redeem Codes',
            'res_model': 'sale.redeem.code.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    # ── ACTION: Send Contract Confirmation Email ───────────────
    def action_send_contract_confirmation(self):
        """
        Kirim email konfirmasi kontrak ke customer.
        Dipanggil otomatis via server action saat state = sale.
        """
        self.ensure_one()
        template = self.env.ref(
            'sale_microcredential.email_template_b2b_contract_confirmed',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
            _logger.info('Contract confirmation email sent for order %s', self.name)

    # ── OVERRIDE: action_confirm ───────────────────────────────
    def action_confirm(self):
        """Override Odoo native confirm untuk trigger workflow B2B."""
        res = super().action_confirm()
        for order in self:
            if order.contract_type == 'B2B_CONTRACT':
                order.contract_start_date = fields.Date.today()
                order.action_send_contract_confirmation()
                _logger.info('B2B Contract %s confirmed, start date set.', order.name)
        return res

    # ── ACTION: Manual Retry Redeem Code (max 3x) ─────────────
    def action_retry_redeem_codes(self):
        """
        Manual retry jika generate redeem code gagal.
        Maksimum 3 percobaan (dicatat di chatter).
        """
        self.ensure_one()
        retry_count = self.message_ids.filtered(
            lambda m: 'RETRY_REDEEM' in (m.subject or '')
        )
        if len(retry_count) >= 3:
            raise UserError(
                'Maksimum 3 kali retry sudah tercapai. '
                'Hubungi tim Website untuk penanganan manual.'
            )
        self.message_post(
            subject='RETRY_REDEEM',
            body=f'Retry request redeem code ke-{len(retry_count) + 1}.',
        )
        return self.action_request_redeem_codes()
```

---

### 5.2 File: `services/__init__.py`

```python
# addons/sale_microcredential/services/__init__.py
from . import redeem_code_service
```

---

### 5.3 File: `services/redeem_code_service.py`

> Ini adalah API client ke Website Group. Gunakan `requests` dan Odoo `base_url` dari `ir.config_parameter`.

```python
# addons/sale_microcredential/services/redeem_code_service.py
import logging
import requests
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REDEEM_API_PATH = '/api/v1/elearning/redeem-codes/generate'
TIMEOUT_SECONDS = 15


class RedeemCodeService(models.AbstractModel):
    """
    Service layer untuk integrasi API dengan Website Group.
    Dipanggil dari wizard atau workflow action.
    """
    _name = 'sale.redeem.code.service'
    _description = 'Redeem Code API Service'

    @api.model
    def generate_codes(self, sale_order, course_id, quantity, expiry_days):
        """
        Kirim POST request ke Website API untuk generate redeem codes.

        :param sale_order: record sale.order
        :param course_id: int, ID dari slide.channel
        :param quantity: int, jumlah kode
        :param expiry_days: int, masa berlaku kode
        :return: dict response dari API atau raise UserError
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'sale_microcredential.website_api_key'
        )
        if not api_key:
            raise UserError(
                'API Key untuk Website tidak ditemukan. '
                'Hubungi administrator untuk setup di Settings → Technical → Parameters.'
            )

        url = f"{base_url.rstrip('/')}{REDEEM_API_PATH}"
        payload = {
            'course_id': course_id,
            'quantity': quantity,
            'contract_id': sale_order.id,
            'contract_reference': sale_order.name,
            'expiry_days': expiry_days,
            'requested_by': self.env.user.login,
        }
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            _logger.error('Timeout saat request redeem code untuk order %s', sale_order.name)
            raise UserError(
                'Request timeout. Coba lagi dalam beberapa menit. '
                'Jika terus gagal, gunakan tombol Retry (maks 3x).'
            )
        except requests.exceptions.RequestException as exc:
            _logger.error('Error request redeem code: %s', exc)
            raise UserError(f'Gagal terhubung ke Website API: {exc}')

        if data.get('status') != 'SUCCESS':
            raise UserError(
                f"Website API merespons error: {data.get('message', 'Unknown error')}"
            )

        # Update sale.order setelah berhasil
        sale_order.write({
            'redeem_codes_generated': True,
            'redeem_code_batch_id': data.get('batch_id'),
            'redeem_codes_generated_at': fields.Datetime.now(),
            'redeem_code_batch_status': 'GENERATED',
        })
        sale_order.message_post(
            body=(
                f"✅ Redeem code berhasil di-generate. "
                f"Batch ID: <b>{data.get('batch_id')}</b>, "
                f"Jumlah: <b>{data.get('codes_generated')}</b>"
            )
        )
        _logger.info(
            'Redeem codes generated for order %s, batch_id=%s',
            sale_order.name,
            data.get('batch_id'),
        )
        return data
```

> **Catatan Keamanan**: API Key disimpan di `ir.config_parameter` (encrypted storage Odoo), tidak di-hardcode. Wajib ikuti ini.

---

### 5.4 File: `wizards/__init__.py`

```python
# addons/sale_microcredential/wizards/__init__.py
from . import redeem_code_wizard
```

---

### 5.5 File: `wizards/redeem_code_wizard.py`

```python
# addons/sale_microcredential/wizards/redeem_code_wizard.py
from odoo import models, fields, api
from odoo.exceptions import UserError


class RedeemCodeWizard(models.TransientModel):
    _name = 'sale.redeem.code.wizard'
    _description = 'Wizard: Generate Redeem Codes'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Kontrak',
        required=True,
        readonly=True,
    )
    # Summary fields (read-only, untuk konfirmasi user)
    partner_name = fields.Char(
        string='Customer',
        related='sale_order_id.partner_id.name',
        readonly=True,
    )
    total_codes = fields.Integer(
        string='Total Kode yang Akan Di-generate',
        compute='_compute_total_codes',
        readonly=True,
    )
    confirmation_note = fields.Text(
        string='Catatan Tambahan',
        help='Opsional: catatan untuk dikirim bersama email distribusi.',
    )

    @api.depends('sale_order_id')
    def _compute_total_codes(self):
        for wiz in self:
            wiz.total_codes = sum(
                wiz.sale_order_id.order_line.mapped('redeem_code_count')
            )

    def action_generate(self):
        """Eksekusi generate untuk semua line B2B pada order."""
        self.ensure_one()
        order = self.sale_order_id
        service = self.env['sale.redeem.code.service']

        if self.total_codes <= 0:
            raise UserError(
                'Tidak ada jumlah kode yang valid pada line order. '
                'Pastikan kolom "Jumlah Redeem Code" sudah diisi.'
            )

        # Update status ke PENDING sebelum request
        order.write({
            'redeem_codes_requested_at': fields.Datetime.now(),
            'redeem_code_batch_status': 'PENDING',
        })

        try:
            for line in order.order_line.filtered(lambda l: l.slide_channel_id and l.redeem_code_count > 0):
                service.generate_codes(
                    sale_order=order,
                    course_id=line.slide_channel_id.id,  # KOREKSI: slide_channel_id bukan course_id
                    quantity=line.redeem_code_count,
                    expiry_days=line.redeem_code_expiry_days,
                )
        except Exception:
            order.write({'redeem_code_batch_status': 'FAILED'})
            raise

        return {'type': 'ir.actions.act_window_close'}
```

---

### 5.6 File: `wizards/wizard_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_redeem_code_wizard_form" model="ir.ui.view">
        <field name="name">sale.redeem.code.wizard.form</field>
        <field name="model">sale.redeem.code.wizard</field>
        <field name="arch" type="xml">
            <form string="Generate Redeem Codes">
                <group>
                    <field name="sale_order_id" invisible="1"/>
                    <field name="partner_name"/>
                    <field name="total_codes"/>
                    <field name="confirmation_note"/>
                </group>
                <footer>
                    <button name="action_generate" type="object"
                            string="Generate Sekarang" class="btn-primary"/>
                    <button string="Batal" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

---

### 5.7 File: `data/email_templates.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">

        <!-- Template: Konfirmasi Kontrak B2B -->
        <record id="email_template_b2b_contract_confirmed" model="mail.template">
            <field name="name">B2B Contract — Konfirmasi Kontrak</field>
            <field name="model_id" ref="sale.model_sale_order"/>
            <field name="subject">Konfirmasi Kontrak: {{ object.name }}</field>
            <field name="email_to">{{ object.partner_id.email }}</field>
            <field name="body_html"><![CDATA[
                <p>Yth. {{ object.partner_id.name }},</p>
                <p>Kontrak <strong>{{ object.name }}</strong> telah dikonfirmasi.</p>
                <p>Periode: {{ object.contract_start_date }} s/d {{ object.expiry_date }}</p>
                <p>Redeem code akan dikirimkan setelah proses generate selesai.</p>
                <p>Salam,<br/>Tim Sales IMPC</p>
            ]]></field>
            <field name="auto_delete" eval="True"/>
        </record>

        <!-- Template: Distribusi Redeem Code -->
        <record id="email_template_redeem_code_ready" model="mail.template">
            <field name="name">B2B Contract — Redeem Code Siap</field>
            <field name="model_id" ref="sale.model_sale_order"/>
            <field name="subject">Redeem Code Siap: Kontrak {{ object.name }}</field>
            <field name="email_to">{{ object.partner_id.email }}</field>
            <field name="body_html"><![CDATA[
                <p>Yth. {{ object.partner_id.name }},</p>
                <p>Redeem code untuk kontrak <strong>{{ object.name }}</strong>
                   (Batch: {{ object.redeem_code_batch_id }}) telah siap.</p>
                <p>Silakan unduh via portal HR Anda atau hubungi sales kami.</p>
            ]]></field>
            <field name="auto_delete" eval="True"/>
        </record>

    </data>
</odoo>
```

---

### 5.8 File: `data/server_actions.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Automated Action: Kirim email konfirmasi saat sale order confirmed -->
        <record id="action_auto_contract_email" model="base.automation">
            <field name="name">B2B: Kirim Email Konfirmasi Saat Kontrak Confirmed</field>
            <field name="model_id" ref="sale.model_sale_order"/>
            <field name="trigger">on_write</field>
            <field name="filter_pre_domain">[('contract_type', '=', 'B2B_CONTRACT')]</field>
            <field name="filter_domain">[('state', '=', 'sale'), ('contract_type', '=', 'B2B_CONTRACT')]</field>
            <field name="action_server_ids" eval="[(4, ref('sale_microcredential.action_server_send_b2b_email'))]"/>
        </record>

        <record id="action_server_send_b2b_email" model="ir.actions.server">
            <field name="name">Send B2B Contract Confirmation Email</field>
            <field name="model_id" ref="sale.model_sale_order"/>
            <field name="binding_model_id" ref="sale.model_sale_order"/>
            <field name="state">code</field>
            <field name="code">
for record in records:
    record.action_send_contract_confirmation()
            </field>
        </record>
    </data>
</odoo>
```

---

### 5.9 File: `data/ir_cron.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Cron: Flag kontrak yang mendekati expiry (jalankan tiap hari) -->
        <record id="ir_cron_flag_renewal_contracts" model="ir.cron">
            <field name="name">Sales: Flag Kontrak yang Akan Expired</field>
            <field name="model_id" ref="sale.model_sale_order"/>
            <field name="state">code</field>
            <field name="code">
from datetime import date, timedelta
today = date.today()
threshold = today + timedelta(days=30)
expiring = env['sale.order'].search([
    ('state', '=', 'sale'),
    ('contract_type', '=', 'B2B_CONTRACT'),
    ('expiry_date', '!=', False),
    ('expiry_date', '&lt;=', threshold),
    ('renewal_opportunity', '=', False),
])
expiring.write({'renewal_opportunity': True})
            </field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="numbercall">-1</field>
            <field name="active" eval="True"/>
        </record>
    </data>
</odoo>
```

---

### 5.10 File: `report/sale_contract_report_action.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Report Action untuk PDF Kontrak B2B -->
    <report
        id="action_report_sale_b2b_contract"
        model="sale.order"
        string="Kontrak B2B PDF"
        report_type="qweb-pdf"
        name="sale_microcredential.report_sale_b2b_contract"
        file="sale_microcredential.report_sale_b2b_contract"
        print_report_name="'Kontrak B2B - %s' % (object.name)"
    />
</odoo>
```

---

### 5.11 Checklist Dev 2

- [ ] Pull terbaru dari `dev/sales-group` setelah Dev 1 push
- [ ] Buat file `services/__init__.py` dan `services/redeem_code_service.py`
- [ ] Isi `models/sale_order_workflow.py` (override stub dari Dev 1)
- [ ] Buat `wizards/__init__.py`, `wizards/redeem_code_wizard.py`, `wizards/wizard_views.xml`
- [ ] Buat `data/email_templates.xml`
- [ ] Buat `data/server_actions.xml`
- [ ] Buat `data/ir_cron.xml`
- [ ] Buat `report/sale_contract_report_action.xml`
- [ ] Test: generate redeem code wizard bisa dibuka dari form order
- [ ] Test: email konfirmasi terkirim saat order dikonfirmasi
- [ ] Test: cron berjalan dan flag `renewal_opportunity` ter-update
- [ ] **Kirim daftar path file ke Dev 1** agar dimasukkan ke `__manifest__.py`

---

## 6. DEV 3 — Views, Portal & Report

**Estimasi**: 4 hari  
**Branch**: `dev/sales-dev3-views`  
**Mulai**: Setelah Dev 1 push models (pull dulu dari `dev/sales-group`)  
**File yang BOLEH disentuh**: Hanya file dalam list berikut — JANGAN edit file milik Dev 1 atau Dev 2.

### File Milik Dev 3 (EKSKLUSIF):

```
views/sale_order_views.xml
views/res_partner_views.xml
views/dashboard_views.xml
controllers/__init__.py
controllers/portal_contract.py
templates/portal_contract_list.xml
templates/portal_contract_detail.xml
templates/portal_redeem_codes.xml
report/sale_contract_report_template.xml
```

---

### 6.1 File: `controllers/__init__.py`

```python
# addons/sale_microcredential/controllers/__init__.py
from . import portal_contract
```

---

### 6.2 File: `controllers/portal_contract.py`

```python
# addons/sale_microcredential/controllers/portal_contract.py
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class HRPartnerPortal(CustomerPortal):
    """
    Portal controller untuk HR partner B2B.
    Extends CustomerPortal agar dapat menggunakan /my/ routes.
    """

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'contract_count' in counters:
            domain = self._get_contracts_domain()
            values['contract_count'] = request.env['sale.order'].search_count(domain)
        return values

    def _get_contracts_domain(self):
        """Domain filter: hanya tampilkan kontrak milik partner yang login."""
        partner = request.env.user.partner_id
        return [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('contract_type', '=', 'B2B_CONTRACT'),
            ('state', 'in', ['sale', 'done']),
        ]

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, **kw):
        domain = self._get_contracts_domain()
        Contract = request.env['sale.order']
        contract_count = Contract.search_count(domain)

        pager = portal_pager(
            url='/my/contracts',
            total=contract_count,
            page=page,
            step=10,
        )
        contracts = Contract.search(domain, limit=10, offset=pager['offset'],
                                    order='date_order desc')
        return request.render(
            'sale_microcredential.portal_my_contracts',
            {'contracts': contracts, 'pager': pager, 'page_name': 'contract'},
        )

    @http.route('/my/contracts/<int:order_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, order_id, **kw):
        order = request.env['sale.order'].browse(order_id)
        # Security check: pastikan partner yang login boleh lihat kontrak ini
        if order.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/contracts')
        return request.render(
            'sale_microcredential.portal_contract_detail',
            {'order': order, 'page_name': 'contract'},
        )
```

---

### 6.3 File: `views/sale_order_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Extend Form View: sale.order -->
    <record id="view_sale_order_form_microcredential" model="ir.ui.view">
        <field name="name">sale.order.form.microcredential</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Tambahkan tab B2B Contract di bawah tab Order Lines -->
            <xpath expr="//notebook" position="inside">
                <page string="Kontrak B2B" name="b2b_contract"
                      invisible="contract_type != 'B2B_CONTRACT'">
                    <group>
                        <group string="Tipe Kontrak">
                            <field name="contract_type"/>
                            <field name="partner_type"/>
                        </group>
                        <group string="Periode Kontrak">
                            <field name="contract_start_date"/>
                            <field name="expiry_date"/>
                            <field name="renewal_opportunity" widget="boolean_toggle"/>
                        </group>
                    </group>
                    <group string="Status Redeem Code">
                        <field name="redeem_code_batch_status"/>
                        <field name="redeem_code_batch_id" readonly="1"/>
                        <field name="redeem_codes_requested_at" readonly="1"/>
                        <field name="redeem_codes_generated_at" readonly="1"/>
                    </group>
                    <div>
                        <!-- Tombol Generate Redeem Code -->
                        <button name="action_request_redeem_codes"
                                type="object"
                                string="Generate Redeem Codes"
                                class="btn-primary"
                                invisible="redeem_codes_generated or contract_type != 'B2B_CONTRACT'"/>
                        <button name="action_retry_redeem_codes"
                                type="object"
                                string="Retry Generate"
                                class="btn-warning"
                                invisible="redeem_code_batch_status != 'FAILED'"/>
                    </div>
                </page>
            </xpath>

            <!-- Tambah kolom pada order lines untuk B2B -->
            <xpath expr="//field[@name='order_line']/tree" position="inside">
                <field name="slide_channel_id" optional="show"/>  <!-- KOREKSI: bukan course_id -->
                <field name="learning_mode" optional="show" readonly="1"/>
                <field name="redeem_code_count" optional="show"/>
                <field name="redeem_code_expiry_days" optional="show"/>
                <field name="student_count" optional="show"/>
            </xpath>

        </field>
    </record>

    <!-- List View: filter kontrak B2B -->
    <record id="view_sale_order_list_microcredential" model="ir.ui.view">
        <field name="name">sale.order.list.microcredential</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_quotation_tree_with_onboarding"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="after">
                <field name="contract_type" optional="show"/>
                <field name="redeem_code_batch_status" optional="show"/>
            </xpath>
        </field>
    </record>

    <!-- Action: Daftar Kontrak B2B -->
    <record id="action_sale_b2b_contracts" model="ir.actions.act_window">
        <field name="name">Kontrak B2B</field>
        <field name="res_model">sale.order</field>
        <field name="view_mode">tree,form</field>
        <field name="domain">[('contract_type', '=', 'B2B_CONTRACT')]</field>
        <field name="context">{'default_contract_type': 'B2B_CONTRACT'}</field>
    </record>

    <!-- Menu: Sales > B2B Contracts -->
    <menuitem
        id="menu_sale_b2b_contracts"
        name="Kontrak B2B"
        parent="sale.sale_order_menu"
        action="action_sale_b2b_contracts"
        sequence="20"/>
</odoo>
```

---

### 6.4 File: `views/res_partner_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Extend Partner Form: tambahkan tab Microcredential -->
    <record id="view_partner_form_microcredential" model="ir.ui.view">
        <field name="name">res.partner.form.microcredential</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <xpath expr="//notebook" position="inside">
                <page string="Microcredential B2B" name="microcredential_b2b">
                    <group>
                        <group string="Klasifikasi Partner">
                            <field name="company_type_microcredential"/>
                            <field name="industry_type"/>
                            <!-- KOREKSI: is_hr_partner_admin ADA di res.users, bukan res.partner -->
                            <!-- Tampilkan di form Settings → Users, bukan di partner form -->
                        </group>
                        <group string="Info Perusahaan">
                            <field name="employee_count"/>
                            <field name="training_budget_annual"
                                   widget="monetary"
                                   options="{'currency_field': 'currency_id'}"/>
                        </group>
                    </group>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

---

### 6.5 File: `views/dashboard_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Dashboard: B2B Contract Performance -->
    <record id="view_sale_b2b_dashboard" model="ir.ui.view">
        <field name="name">sale.order.b2b.dashboard</field>
        <field name="model">sale.order</field>
        <field name="arch" type="xml">
            <pivot string="Performa Kontrak B2B">
                <field name="partner_id" type="row"/>
                <field name="expiry_date" type="col" interval="month"/>
                <field name="amount_total" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_sale_b2b_graph" model="ir.ui.view">
        <field name="name">sale.order.b2b.graph</field>
        <field name="model">sale.order</field>
        <field name="arch" type="xml">
            <graph string="Kontrak B2B — Revenue" type="bar">
                <field name="partner_id" type="row"/>
                <field name="amount_total" type="measure"/>
            </graph>
        </field>
    </record>

    <record id="action_sale_b2b_dashboard" model="ir.actions.act_window">
        <field name="name">Dashboard Kontrak B2B</field>
        <field name="res_model">sale.order</field>
        <field name="view_mode">graph,pivot,tree</field>
        <field name="domain">[('contract_type', '=', 'B2B_CONTRACT')]</field>
    </record>

    <menuitem
        id="menu_sale_b2b_dashboard"
        name="Dashboard B2B"
        parent="sale.sale_order_menu"
        action="action_sale_b2b_dashboard"
        sequence="30"/>
</odoo>
```

---

### 6.6 File: `templates/portal_contract_list.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="portal_my_contracts" name="Portal: Daftar Kontrak HR">
        <t t-call="portal.portal_layout">
            <t t-set="breadcrumbs_searchbar" t-value="True"/>
            <t t-call="portal.portal_searchbar">
                <t t-set="title">Kontrak B2B Saya</t>
            </t>

            <t t-if="not contracts">
                <div class="alert alert-info">
                    Belum ada kontrak aktif.
                </div>
            </t>

            <t t-if="contracts">
                <table class="table table-hover o_portal_my_doc_table">
                    <thead>
                        <tr>
                            <th>No. Kontrak</th>
                            <th>Mulai</th>
                            <th>Berakhir</th>
                            <th>Status Kode</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="contracts" t-as="contract">
                            <tr>
                                <td>
                                    <a t-attf-href="/my/contracts/{{ contract.id }}">
                                        <t t-esc="contract.name"/>
                                    </a>
                                </td>
                                <td><t t-esc="contract.contract_start_date"/></td>
                                <td><t t-esc="contract.expiry_date"/></td>
                                <td>
                                    <span t-attf-class="badge #{
                                        'bg-success' if contract.redeem_code_batch_status == 'GENERATED'
                                        else 'bg-warning' if contract.redeem_code_batch_status == 'PENDING'
                                        else 'bg-danger'
                                    }">
                                        <t t-esc="contract.redeem_code_batch_status or 'N/A'"/>
                                    </span>
                                </td>
                                <td>
                                    <t t-esc="contract.currency_id.symbol"/>
                                    <t t-esc="'{:,.0f}'.format(contract.amount_total)"/>
                                </td>
                            </tr>
                        </t>
                    </tbody>
                </table>
                <t t-call="portal.pager" t-value="pager"/>
            </t>
        </t>
    </template>
</odoo>
```

---

### 6.7 File: `templates/portal_contract_detail.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="portal_contract_detail" name="Portal: Detail Kontrak">
        <t t-call="portal.portal_layout">
            <div class="container mt-4">
                <h3>Kontrak: <t t-esc="order.name"/></h3>
                <div class="row">
                    <div class="col-md-6">
                        <dl class="row">
                            <dt class="col-sm-5">Customer</dt>
                            <dd class="col-sm-7"><t t-esc="order.partner_id.name"/></dd>
                            <dt class="col-sm-5">Mulai</dt>
                            <dd class="col-sm-7"><t t-esc="order.contract_start_date"/></dd>
                            <dt class="col-sm-5">Berakhir</dt>
                            <dd class="col-sm-7"><t t-esc="order.expiry_date"/></dd>
                            <dt class="col-sm-5">Batch ID</dt>
                            <dd class="col-sm-7">
                                <t t-esc="order.redeem_code_batch_id or 'Belum di-generate'"/>
                            </dd>
                        </dl>
                    </div>
                </div>

                <h5 class="mt-4">Kursus &amp; Redeem Code</h5>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Kursus</th>
                            <th>Mode</th>
                            <th>Jumlah Kode</th>
                            <th>Durasi Akses</th>
                            <th>Jadwal Sesi (Hybrid)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="order.order_line" t-as="line">
                            <tr t-if="line.slide_channel_id">  <!-- KOREKSI: slide_channel_id -->
                                <td><t t-esc="line.slide_channel_id.name"/></td>
                                <td><t t-esc="line.learning_mode"/></td>
                                <td><t t-esc="line.redeem_code_count"/></td>
                                <td><t t-esc="line.course_access_duration_days"/> hari</td>
                                <td>
                                    <t t-if="line.learning_mode == 'HYBRID'">
                                        <t t-esc="line.hybrid_session_summary or 'Info menyusul'"/>
                                    </t>
                                    <t t-else="">—</t>
                                </td>
                            </tr>
                        </t>
                    </tbody>
                </table>

                <a href="/my/contracts" class="btn btn-secondary mt-3">← Kembali</a>
            </div>
        </t>
    </template>
</odoo>
```

---

### 6.8 File: `templates/portal_redeem_codes.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!--
        Template ini untuk menampilkan daftar redeem code (dari batch_id).
        Data aktual kode diambil dari Website Group via API — template ini
        hanya menampilkan metadata batch dan link download CSV.
        Koordinasikan format response dengan Website Group.
    -->
    <template id="portal_redeem_codes" name="Portal: Redeem Codes">
        <t t-call="portal.portal_layout">
            <div class="container mt-4">
                <h3>Redeem Codes — <t t-esc="order.name"/></h3>

                <div class="alert alert-info">
                    <strong>Batch ID:</strong> <t t-esc="order.redeem_code_batch_id"/><br/>
                    <strong>Di-generate:</strong> <t t-esc="order.redeem_codes_generated_at"/><br/>
                    <em>Kode ditampilkan 4 karakter pertama saja untuk keamanan.</em>
                </div>

                <!-- Download CSV -->
                <t t-if="order.redeem_codes_generated">
                    <a t-attf-href="/api/v1/elearning/redeem-codes/download/#{order.redeem_code_batch_id}"
                       class="btn btn-primary mb-3" target="_blank">
                        Download CSV Redeem Codes
                    </a>
                </t>
                <t t-else="">
                    <div class="alert alert-warning">
                        Redeem code belum di-generate. Hubungi sales manager Anda.
                    </div>
                </t>

                <a href="/my/contracts" class="btn btn-secondary">← Kembali</a>
            </div>
        </t>
    </template>
</odoo>
```

---

### 6.9 File: `report/sale_contract_report_template.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="report_sale_b2b_contract">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="o">
                <t t-call="web.external_layout">
                    <div class="page">
                        <h2>KONTRAK B2B MICROCREDENTIAL</h2>
                        <h3><t t-esc="o.name"/></h3>

                        <table class="table table-sm mt-4">
                            <tr>
                                <td><strong>Customer</strong></td>
                                <td><t t-esc="o.partner_id.name"/></td>
                            </tr>
                            <tr>
                                <td><strong>Periode</strong></td>
                                <td>
                                    <t t-esc="o.contract_start_date"/> —
                                    <t t-esc="o.expiry_date"/>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Total Nilai</strong></td>
                                <td>
                                    <t t-esc="o.currency_id.symbol"/>
                                    <t t-esc="'{:,.0f}'.format(o.amount_total)"/>
                                </td>
                            </tr>
                        </table>

                        <h5>Detail Kursus</h5>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Kursus</th>
                                    <th>Mode</th>
                                    <th>Jumlah Peserta</th>
                                    <th>Kode Redeem</th>
                                    <th>Harga Satuan</th>
                                    <th>Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="o.order_line" t-as="line">
                                    <tr>
                                        <td>
                                            <!-- KOREKSI: slide_channel_id bukan course_id -->
                                            <t t-esc="line.slide_channel_id.name if line.slide_channel_id else line.name"/>
                                        </td>
                                        <td><t t-esc="line.learning_mode or '—'"/></td>
                                        <td><t t-esc="line.student_count"/></td>
                                        <td><t t-esc="line.redeem_code_count"/></td>
                                        <td>
                                            <t t-esc="o.currency_id.symbol"/>
                                            <t t-esc="'{:,.0f}'.format(line.price_unit)"/>
                                        </td>
                                        <td>
                                            <t t-esc="o.currency_id.symbol"/>
                                            <t t-esc="'{:,.0f}'.format(line.price_subtotal)"/>
                                        </td>
                                    </tr>
                                    <!-- Sesi Hybrid (jika ada) -->
                                    <tr t-if="line.learning_mode == 'HYBRID' and line.hybrid_session_summary">
                                        <td colspan="6" class="text-muted small">
                                            Jadwal Sesi Tatap Muka:
                                            <t t-esc="line.hybrid_session_summary"/>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>

                        <div class="mt-5 row">
                            <div class="col-6 text-center">
                                <p>Pihak Perusahaan</p>
                                <br/><br/><br/>
                                <p>(_____________________)</p>
                            </div>
                            <div class="col-6 text-center">
                                <p>IMPC Sales Manager</p>
                                <br/><br/><br/>
                                <p>(_____________________)</p>
                            </div>
                        </div>
                    </div>
                </t>
            </t>
        </t>
    </template>
</odoo>
```

---

### 6.10 Checklist Dev 3

- [ ] Pull terbaru dari `dev/sales-group` setelah Dev 1 push
- [ ] Buat `controllers/__init__.py` dan `controllers/portal_contract.py`
- [ ] Buat `views/sale_order_views.xml` (termasuk tombol yang memanggil method Dev 2)
- [ ] Buat `views/res_partner_views.xml`
- [ ] Buat `views/dashboard_views.xml`
- [ ] Buat `templates/portal_contract_list.xml`
- [ ] Buat `templates/portal_contract_detail.xml`
- [ ] Buat `templates/portal_redeem_codes.xml`
- [ ] Buat `report/sale_contract_report_template.xml`
- [ ] Test: Form sale.order menampilkan tab "Kontrak B2B" saat `contract_type = B2B_CONTRACT`
- [ ] Test: Portal `/my/contracts` dapat diakses oleh user dengan group `HR Partner`
- [ ] Test: PDF kontrak ter-generate dari tombol Print
- [ ] **Kirim daftar path file ke Dev 1** agar dimasukkan ke `__manifest__.py`

---

## 7. Urutan Pengerjaan & Dependency Matrix

```
HARI 1─3: DEV 1 (ALONE)
  ┌─────────────────────────────────────────────┐
  │ Buat scaffold + models + security           │
  │ Push ke dev/sales-dev1-models               │
  │ Merge ke dev/sales-group                    │
  │ NOTIFY Dev 2 & Dev 3: "models sudah ready"  │
  └─────────────────────────────────────────────┘

HARI 4─7: DEV 2 & DEV 3 (PARALEL, INDEPENDEN)
  ┌─────────────────────────┐   ┌─────────────────────────┐
  │ DEV 2                   │   │ DEV 3                   │
  │ Pull dari dev/sales-group│   │ Pull dari dev/sales-group│
  │ Kerjakan workflow,      │   │ Kerjakan views, portal, │
  │ services, wizards, data │   │ controllers, templates  │
  │ TIDAK edit file Dev 1   │   │ TIDAK edit file Dev 1   │
  │ TIDAK edit file Dev 3   │   │ TIDAK edit file Dev 2   │
  └─────────────────────────┘   └─────────────────────────┘

HARI 8: MERGE DAY
  1. Dev 2 PR → dev/sales-group (merge dulu)
  2. Dev 3 PR → dev/sales-group (merge setelah Dev 2)
  3. Dev 1 update __manifest__.py dengan semua file baru
  4. Full integration test (semua 3 dev)

HARI 9─10: BUGFIX & POLISH
  Tiap dev fix bug di file miliknya sendiri.
```

### Dependency Matrix

| Tugas | Depends On | Dev |
|---|---|---|
| Scaffold & models | — | Dev 1 |
| Security | Scaffold | Dev 1 |
| Workflow methods | `sale_order.py` fields (Dev 1) | Dev 2 |
| API Service | `sale_order.py` fields (Dev 1) | Dev 2 |
| Wizard | API Service (Dev 2) | Dev 2 |
| Email Templates | — | Dev 2 |
| Server Actions | `sale_order_workflow.py` methods (Dev 2) | Dev 2 |
| Backend Views | `sale_order.py` fields (Dev 1) | Dev 3 |
| Portal Controller | `sale_order.py` fields (Dev 1) | Dev 3 |
| Portal Templates | Portal Controller (Dev 3) | Dev 3 |
| Report Template | fields (Dev 1) | Dev 3 |
| Manifest (final) | Semua file | Dev 1 |

---

## 8. Testing Checklist (Shared)

Setelah semua di-merge, **semua developer wajib test bersama**:

### Skenario Test 1: B2B Contract Full Flow
- [ ] Buat sale.order baru dengan `contract_type = B2B_CONTRACT`
- [ ] Tambah order line dengan `slide_channel_id` (FK ke `slide.channel`) dan `redeem_code_count = 10`  <!-- KOREKSI: bukan course_id -->
- [ ] Confirm order → pastikan email konfirmasi terkirim
- [ ] Klik tombol "Generate Redeem Codes" → wizard muncul
- [ ] Cek `redeem_code_batch_status` berubah ke `PENDING`
- [ ] (Mock API) Cek status berubah ke `GENERATED` setelah mock response

### Skenario Test 2: Portal HR Partner
- [ ] Buat user portal dengan group `HR Partner`
- [ ] Login ke `/my/contracts` → lihat daftar kontrak
- [ ] Klik ke detail kontrak → tampil info benar
- [ ] Untuk kontrak hybrid: jadwal sesi tampil (atau "Info menyusul")

### Skenario Test 3: PDF Report
- [ ] Buka sale.order B2B yang sudah confirmed
- [ ] Klik Print → Kontrak B2B PDF
- [ ] PDF ter-generate dengan format yang benar

### Skenario Test 4: Renewal Cron
- [ ] Set `expiry_date` kontrak ke H+15 dari hari ini
- [ ] Jalankan cron manual dari Settings → Technical → Automation → Scheduled Actions
- [ ] Pastikan `renewal_opportunity = True` ter-update

### Skenario Test 5: Security
- [ ] Pastikan user `HR Partner` **tidak bisa** edit sale.order (read-only)
- [ ] Pastikan user `HR Partner` hanya melihat kontrak milik perusahaannya sendiri

---

## 9. FAQ & Konvensi Kode

### Q: Model `slide.channel` atau `elearning.course`?
**A**: Di Odoo 19, model eLearning adalah `slide.channel`. Gunakan `slide_channel_id` (bukan `course_id`) sebagai nama field di `sale.order.line`. Field `course_id` TIDAK digunakan — ini konsisten dengan PRD Sales Group.

### Q: Bagaimana kalau API Website belum ready saat dev?
**A**: Gunakan mock di lokal. Tambahkan `ir.config_parameter` dengan key `sale_microcredential.mock_api = True`, lalu di `redeem_code_service.py` tambahkan kondisi:
```python
if self.env['ir.config_parameter'].sudo().get_param('sale_microcredential.mock_api') == 'True':
    # return mock response untuk testing
    return {'status': 'SUCCESS', 'batch_id': 'MOCK-001', 'codes_generated': 10, 'csv_url': '#'}
```

### Q: Bagaimana cara menjalankan Odoo lokal?
```bash
# Di folder sistem-microcredential-hybrid
docker-compose up -d
# Buka browser: http://localhost:8069
# Install modul: Settings → Apps → Cari "sale_microcredential"
```

### Q: Bagaimana cara update modul setelah edit file?
```bash
# Di container Odoo
docker-compose exec web odoo -u sale_microcredential --stop-after-init
```

### Q: Konvensi penamaan file Python
- Model files: `nama_model.py` (snake_case)
- Method names: `action_*` untuk button actions, `_compute_*` untuk compute, `_onchange_*` untuk onchange
- XML IDs: `<modul>.<tipe>_<nama>` contoh: `sale_microcredential.view_sale_order_form_microcredential`

### Q: Siapa yang fix kalau ada import error di `models/__init__.py`?
**A**: **Dev 1** yang bertanggung jawab atas file `__init__.py`. Kalau ada error karena file baru Dev 2 atau Dev 3, koordinasi ke Dev 1.

### Q: Bagaimana kalau ada conflict saat merge?
**A**: Conflict tidak seharusnya terjadi kalau pembagian file diikuti. Jika tetap terjadi:
1. Hubungi dev yang punya file tersebut
2. Jangan pernah resolve conflict sendiri di file milik dev lain
3. Resolve bersama via video call

---

*Dokumen ini disiapkan untuk tim Sales Group — IMPC Microcredential Platform.*  
*Update terakhir: Mei 2026*