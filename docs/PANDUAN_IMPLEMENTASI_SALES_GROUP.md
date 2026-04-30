# Panduan Implementasi Sales Group — 3 Developer
**Proyek**: Sistem Microcredential Hybrid IMPC  
**Modul**: Sales, CRM, Contacts (Odoo)  
**Referensi PRD**: PRD Sales Group v1.0  
**Tanggal**: April 2026

---

## RINGKASAN PEMBAGIAN TUGAS

| Developer | Peran | Domain Utama | File yang Dimiliki |
|---|---|---|---|
| **Dev 1** | Contract Core | B2B quotation, contract fields, state machine, email template, PDF quotation | `sale_order_contract.py`, `sale_order_line_contract.py`, views contract, mail template, report PDF |
| **Dev 2** | Integration & API | Learning mode sync, hybrid summary, redeem code API client, audit log | `sale_order_integration.py`, `redeem_code_log.py`, API client, wizard redeem code, views integration |
| **Dev 3** | CRM, Portal & Dashboard | Partner/CRM extension, portal HR, renewal workflow, performance dashboard | `res_partner_extended.py`, `sale_order_renewal.py`, portal controller, portal templates, CRM data, dashboard |

> **Aturan Emas**: Setiap developer hanya boleh edit file yang ada di domain-nya. Jika butuh perubahan di file lain, buat issue/ticket dulu dan koordinasikan — JANGAN langsung edit file milik developer lain.

---

## PENDEKATAN TEKNIS: Custom Add-on dengan `_inherit` (BUKAN Modifikasi Core)

### Pertanyaan Kritis: Buat Modul Baru atau Modifikasi Modul Existing?

**Jawaban: Selalu buat custom add-on baru, gunakan `_inherit` untuk extend modul existing.**

Ini bukan preferensi — ini adalah **aturan fundamental Odoo** yang tidak boleh dilanggar:

| Pendekatan | Cara | Boleh? | Alasan |
|---|---|---|---|
| ✅ **Custom add-on + `_inherit`** | Buat `microcredential_sales/`, extend model via `_inherit` | **YA** | Best practice Odoo, upgrade-safe, tidak rusak core |
| ❌ **Edit modul core Odoo** | Edit langsung file di `addons/sale/models/sale_order.py` | **TIDAK** | Rusak saat upgrade Odoo, konflik dengan patch resmi |
| ❌ **Duplikasi modul core** | Copy folder `sale/` dan modifikasi | **TIDAK** | Kehilangan semua update Odoo, dependency hell |

### Bagaimana `_inherit` Bekerja

```
Odoo Core (sale.order)          Custom Add-on (microcredential_sales)
────────────────────────         ──────────────────────────────────────
sale/models/sale_order.py        models/sale_order_contract.py
class SaleOrder:                 class SaleOrderContract:
    name = ...                       _inherit = 'sale.order'   ← Extend, bukan replace
    partner_id = ...                 contract_type = ...       ← Field baru ditambahkan
    action_confirm() {...}           action_confirm() {        ← Method di-override
                                         super().action_confirm()  ← Core tetap berjalan
                                         ...tambahan logic...
                                     }
```

Saat Odoo loading, semua class dengan `_inherit = 'sale.order'` **digabung** ke dalam satu class `sale.order` di runtime via Python MRO. Core tidak diubah sama sekali.

### Kapan Pakai `_inherit` vs `_name`

| Situasi | Gunakan | Contoh di proyek ini |
|---|---|---|
| Tambahkan field ke model existing | `_inherit` | Tambah `contract_type` ke `sale.order` |
| Override method di model existing | `_inherit` | Override `action_confirm` di `sale.order` |
| Buat model **baru** dari nol | `_name` | `redeem.code.request.log` (bukan turunan model mana pun) |
| Buat transient wizard baru | `_name` + `_inherit = 'models.TransientModel'` | `redeem.code.wizard` |
| Extend view XML existing | `inherit_id` di view XML | Tambah tab B2B di form `sale.order` |

### Struktur inheritance di modul ini

```
sale.order (Odoo core)
├── SaleOrderContract      (_inherit)  ← Dev 1: contract fields + approval
├── SaleOrderRedeemIntegration (_inherit) ← Dev 2: redeem code fields + API
└── SaleOrderRenewal       (_inherit)  ← Dev 3: renewal fields + cron

sale.order.line (Odoo core)
├── SaleOrderLineContract  (_inherit)  ← Dev 1: course_id, student_count
└── SaleOrderLine          (_inherit)  ← Dev 2: learning_mode, hybrid_summary

res.partner (Odoo core)
└── ResPartnerExtended     (_inherit)  ← Dev 3: company_type, hr portal fields

redeem.code.request.log    (_name)     ← Dev 2: model BARU (bukan inherit)
redeem.code.wizard         (_name)     ← Dev 2: transient wizard BARU
```

> **Mengapa boleh banyak class inherit model yang sama?** Karena Odoo membangun MRO (Method Resolution Order) secara dinamis. Semua class yang `_inherit = 'sale.order'` akan digabung menjadi satu class di runtime — tidak ada konflik selama nama field/method tidak sama. Jika ada method yang sama (seperti `action_confirm`), Odoo menyusunnya berurutan via Python MRO dan setiap class bertanggung jawab memanggil `super()`.

---

## STRUKTUR MODUL ODOO

Buat satu Odoo add-on baru bernama `microcredential_sales`:

```
microcredential_sales/
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   │
│   │── [DEV 1] sale_order_contract.py          ← Fields kontrak + state machine
│   │── [DEV 1] sale_order_line_contract.py     ← Fields line item (kursus, jumlah student)
│   │
│   │── [DEV 2] sale_order_integration.py       ← Fields learning_mode, hybrid summary, redeem batch
│   │── [DEV 2] redeem_code_log.py              ← Model audit log API redeem
│   │
│   │── [DEV 3] res_partner_extended.py         ← Extended fields partner HR
│   └── [DEV 3] sale_order_renewal.py           ← Fields renewal + computed property
│
├── wizard/
│   └── [DEV 2] redeem_code_wizard.py           ← Wizard manual trigger/retry redeem code
│
├── controllers/
│   └── [DEV 3] portal_hr_controller.py         ← Portal views & routes untuk HR manager
│
├── views/
│   │── [DEV 1] sale_order_contract_views.xml
│   │── [DEV 1] sale_order_line_contract_views.xml
│   │── [DEV 2] sale_order_integration_views.xml
│   │── [DEV 2] redeem_code_log_views.xml
│   │── [DEV 3] res_partner_views.xml
│   │── [DEV 3] portal_hr_templates.xml
│   └── [DEV 3] sale_order_dashboard_views.xml
│
├── data/
│   │── [DEV 1] mail_templates.xml              ← Template email contract + redeem CSV
│   └── [DEV 3] crm_pipeline_data.xml           ← Stage CRM B2B
│
├── report/
│   └── [DEV 1] quotation_b2b_report.xml        ← PDF template quotation B2B
│
└── security/
    └── ir.model.access.csv                     ← Dibuat bersama di akhir / Dev 1 koordinasi
```

---

---

# DEV 1 — Contract Core

**Scope**: Membangun pondasi B2B contract: model fields, state machine, approval workflow, email template konfirmasi, dan PDF quotation.

**Dependency**: Bisa mulai dari **hari pertama** (S-01 = PARALEL, tidak perlu tunggu siapapun).

---

## FASE 1 — Setup Modul Dasar (Hari 1)

### Step 1.1 — Buat Struktur Modul Odoo

```bash
# Di dalam direktori addons Odoo kamu
mkdir -p microcredential_sales/{models,views,data,report,security,wizard,controllers}
touch microcredential_sales/__init__.py
touch microcredential_sales/models/__init__.py
```

### Step 1.2 — Buat `__manifest__.py`

```python
# microcredential_sales/__manifest__.py
{
    'name': 'Microcredential Sales',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'B2B Contract Management untuk Platform Microcredential IMPC',
    'author': 'IMPC Dev Team',
    'depends': [
        'sale',        # sale.order, sale.order.line
        'crm',         # crm.stage, pipeline
        'contacts',    # res.partner UI (verified ada di Odoo 17)
        'mail',        # mail.template, chatter
        'portal',      # CustomerPortal, portal views
        'account',     # link ke invoice (A-06)
        'website_slides',  # slide.channel (model kursus eLearning) — field course_id
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'data/crm_pipeline_data.xml',
        'views/sale_order_contract_views.xml',
        'views/sale_order_line_contract_views.xml',
        'views/sale_order_integration_views.xml',
        'views/redeem_code_log_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_dashboard_views.xml',
        'views/portal_hr_templates.xml',
        'report/quotation_b2b_report.xml',
        'wizard/redeem_code_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
```

> **Catatan `depends`**:
> - `website_slides` adalah nama modul resmi Odoo 17 yang menyediakan model `slide.channel` (kursus eLearning). Ini dibutuhkan karena `course_id` di `sale.order.line` adalah FK ke `slide.channel`.
> - `contacts` valid di Odoo 17 (verified di addons reference).
> - Jika Website Group belum install `website_slides` di environment, modul ini akan gagal install. Koordinasikan dengan Website Group.

### Step 1.3 — Buat `models/__init__.py`

```python
# models/__init__.py
from . import sale_order_contract
from . import sale_order_line_contract
from . import sale_order_integration     # Dev 2 akan isi ini
from . import redeem_code_log            # Dev 2 akan isi ini
from . import res_partner_extended       # Dev 3 akan isi ini
from . import sale_order_renewal         # Dev 3 akan isi ini
```

> Buat semua file `.py` sebagai file kosong dulu (`pass`) agar modul bisa di-install. Dev 2 dan Dev 3 akan mengisi file masing-masing.

---

## FASE 2 — Model B2B Contract (Hari 1–2)

### Step 2.1 — Buat `models/sale_order_contract.py`

```python
# models/sale_order_contract.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderContract(models.Model):
    _inherit = 'sale.order'

    # ── Tipe Kontrak ─────────────────────────────────────────────────────────
    contract_type = fields.Selection(
        selection=[
            ('B2C', 'B2C – Individual'),
            ('B2B_CONTRACT', 'B2B – Corporate Contract'),
        ],
        string='Tipe Kontrak',
        default='B2C',
        required=True,
        tracking=True,
    )
    partner_type = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Perusahaan – HR'),
            ('CORPORATE_OTHER', 'Perusahaan – Lainnya'),
        ],
        string='Tipe Partner',
        default='INDIVIDUAL',
        tracking=True,
    )

    # ── Periode Kontrak B2B ──────────────────────────────────────────────────
    contract_start_date = fields.Date(
        string='Tanggal Mulai Kontrak',
        tracking=True,
    )
    contract_end_date = fields.Date(
        string='Tanggal Berakhir Kontrak',
        tracking=True,
    )
    course_access_duration_days = fields.Integer(
        string='Durasi Akses Kursus (hari)',
        default=90,
    )

    # ── Status Approval ──────────────────────────────────────────────────────
    approval_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waiting_approval', 'Menunggu Persetujuan'),
            ('approved', 'Disetujui'),
            ('rejected', 'Ditolak'),
        ],
        string='Status Approval',
        default='draft',
        tracking=True,
        copy=False,
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Disetujui Oleh',
        readonly=True,
        copy=False,
    )
    approved_date = fields.Datetime(
        string='Tanggal Persetujuan',
        readonly=True,
        copy=False,
    )

    # ── Computed: apakah kontrak B2B ─────────────────────────────────────────
    is_b2b_contract = fields.Boolean(
        string='Adalah B2B?',
        compute='_compute_is_b2b',
        store=True,
    )

    @api.depends('contract_type')
    def _compute_is_b2b(self):
        for rec in self:
            rec.is_b2b_contract = rec.contract_type == 'B2B_CONTRACT'

    # ── Aksi Approval ────────────────────────────────────────────────────────
    def action_request_approval(self):
        """Sales kirim ke approver."""
        self.ensure_one()
        if self.contract_type != 'B2B_CONTRACT':
            raise UserError(_('Approval hanya untuk kontrak B2B.'))
        self.approval_state = 'waiting_approval'
        # Kirim notifikasi email ke approver (opsional: tambahkan follower)
        self.message_post(
            body=_('Kontrak B2B menunggu persetujuan: %s') % self.name,
            subtype_xmlid='mail.mt_comment',
        )

    def action_approve_contract(self):
        """Manager menyetujui kontrak."""
        self.ensure_one()
        self.approval_state = 'approved'
        self.approved_by = self.env.user
        self.approved_date = fields.Datetime.now()
        self.message_post(
            body=_('Kontrak disetujui oleh %s') % self.env.user.name,
        )

    def action_reject_contract(self):
        """Manager menolak kontrak."""
        self.ensure_one()
        self.approval_state = 'rejected'
        self.message_post(
            body=_('Kontrak ditolak oleh %s') % self.env.user.name,
        )
```

> **Catatan**: Method `action_confirm` (override penuh) akan ditambahkan di Phase 3 setelah field `contract_status` didefinisikan, karena logic-nya juga mengupdate `contract_status`.

### Step 2.2 — Buat `models/sale_order_line_contract.py`

```python
# models/sale_order_line_contract.py
from odoo import models, fields


class SaleOrderLineContract(models.Model):
    _inherit = 'sale.order.line'

    # ── Referensi Kursus ─────────────────────────────────────────────────────
    course_id = fields.Many2one(
        comodel_name='slide.channel',      # Model kursus di eLearning Odoo
        string='Kursus',
        ondelete='set null',
    )

    # ── Kuantitas Khusus B2B ─────────────────────────────────────────────────
    student_count = fields.Integer(
        string='Jumlah Student',
        default=1,
        help='Jumlah slot student dalam paket B2B',
    )
    redeem_code_count = fields.Integer(
        string='Jumlah Redeem Code',
        help='Otomatis terisi = student_count; bisa diubah',
    )
    redeem_code_expiry_days = fields.Integer(
        string='Masa Berlaku Redeem Code (hari)',
        default=90,
    )

    # ── Catatan Untuk Redeem Code ────────────────────────────────────────────
    redeem_code_notes = fields.Text(
        string='Catatan Redeem Code',
        help='Instruksi distribusi kode untuk HR',
    )
```

---

## FASE 3 — Contract State Machine (Hari 2–3)

Contract mengikuti flow:
```
DRAFT → QUOTATION_SENT → APPROVED → CONFIRMED → ONGOING → COMPLETED
                                              ↘ EXPIRED
                                              ↘ RENEWED
```

Tambahkan field `contract_status` di `sale_order_contract.py`:

```python
# Tambahkan di dalam class SaleOrderContract (setelah field is_b2b_contract)

contract_status = fields.Selection(
    selection=[
        ('draft', 'Draft'),
        ('quotation_sent', 'Quotation Terkirim'),
        ('approved', 'Disetujui Customer'),
        ('confirmed', 'Dikonfirmasi / Aktif'),
        ('ongoing', 'Sedang Berjalan'),
        ('completed', 'Selesai'),
        ('expired', 'Kadaluarsa'),
        ('renewed', 'Diperbarui'),
    ],
    string='Status Kontrak B2B',
    default='draft',
    tracking=True,
    copy=False,
)

def action_send_quotation(self):
    """Kirim quotation ke customer → status quotation_sent."""
    self.ensure_one()
    self.contract_status = 'quotation_sent'
    # Panggil email template quotation (diisi di Step 4)
    template = self.env.ref(
        'microcredential_sales.email_template_b2b_quotation',
        raise_if_not_found=False,
    )
    if template:
        template.send_mail(self.id, force_send=True)

def action_customer_approved(self):
    """Customer menyetujui → tunggu internal confirm."""
    self.ensure_one()
    self.contract_status = 'approved'

def action_set_ongoing(self):
    """Setelah confirmed & redeem code digenerate."""
    self.ensure_one()
    self.contract_status = 'ongoing'

def action_complete_contract(self):
    self.ensure_one()
    self.contract_status = 'completed'

# ── Override action_confirm (Odoo native) ────────────────────────────
def action_confirm(self):
    """
    Override action_confirm standar Odoo.
    Untuk B2B: wajib approval sebelum confirm.
    Setelah confirm: set contract_status = 'confirmed' dan kirim email.

    PENTING — MRO CHAIN:
    Dev 2 juga override action_confirm di SaleOrderRedeemIntegration.
    Karena file sale_order_integration.py di-load SETELAH file ini
    (urutan di models/__init__.py), MRO runtime akan menjadi:
        SaleOrderRedeemIntegration.action_confirm  (dipanggil pertama)
            → super() → SaleOrderContract.action_confirm  (file ini)
                → super() → sale.order.action_confirm  (Odoo native)
    Jadi SELALU pastikan file ini dan sale_order_integration.py
    keduanya memanggil super() agar chain tidak putus.
    """
    for order in self:
        if (
            order.contract_type == 'B2B_CONTRACT'
            and order.approval_state != 'approved'
        ):
            raise UserError(
                _('Kontrak B2B harus disetujui terlebih dahulu sebelum dikonfirmasi.')
            )

    result = super().action_confirm()

    # Update contract_status dan kirim email konfirmasi untuk B2B
    for order in self.filtered(lambda o: o.contract_type == 'B2B_CONTRACT'):
        order.contract_status = 'confirmed'
        template = self.env.ref(
            'microcredential_sales.email_template_b2b_confirmation',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(order.id, force_send=True)

    return result
```

---

## FASE 4 — Email Template (Hari 3)

### Step 4.1 — Buat `data/mail_templates.xml`

```xml
<!-- data/mail_templates.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Template: Quotation B2B -->
    <record id="email_template_b2b_quotation" model="mail.template">
        <field name="name">B2B Quotation – IMPC Microcredential</field>
        <field name="model_id" ref="sale.model_sale_order"/>
        <field name="email_to">{{ object.partner_id.email }}</field>
        <field name="subject">Penawaran Paket Microcredential – {{ object.name }}</field>
        <field name="body_html" type="html">
            <p>Yth. <t t-out="object.partner_id.name"/>,</p>
            <p>Berikut kami sampaikan penawaran paket Microcredential IMPC untuk perusahaan Anda.</p>
            <p>Nomor Quotation: <strong><t t-out="object.name"/></strong></p>
            <p>Nilai Total: <strong><t t-out="object.amount_total"/> IDR</strong></p>
            <p>Berlaku hingga: <t t-out="object.validity_date"/></p>
            <p>Silakan hubungi tim Sales kami untuk konfirmasi lebih lanjut.</p>
            <p>Salam,<br/>Tim Sales IMPC</p>
        </field>
        <field name="lang">{{ object.partner_id.lang }}</field>
        <field name="auto_delete" eval="True"/>
    </record>

    <!-- Template: Contract Confirmation -->
    <record id="email_template_b2b_confirmation" model="mail.template">
        <field name="name">B2B Contract Confirmation – IMPC</field>
        <field name="model_id" ref="sale.model_sale_order"/>
        <field name="email_to">{{ object.partner_id.email }}</field>
        <field name="subject">Konfirmasi Kontrak Microcredential – {{ object.name }}</field>
        <field name="body_html" type="html">
            <p>Yth. <t t-out="object.partner_id.name"/>,</p>
            <p>Kontrak B2B Microcredential IMPC Anda telah <strong>dikonfirmasi</strong>.</p>
            <p>Nomor Kontrak: <strong><t t-out="object.name"/></strong></p>
            <p>Periode Akses: <t t-out="object.contract_start_date"/> s/d <t t-out="object.contract_end_date"/></p>
            <!-- Jika hybrid, tampilkan jadwal sesi offline (diisi oleh Dev 2 via field hybrid_session_summary) -->
            <t t-if="object.order_line.filtered(lambda l: l.learning_mode == 'HYBRID')">
                <p><strong>Informasi Sesi Tatap Muka (Hybrid):</strong></p>
                <t t-foreach="object.order_line.filtered(lambda l: l.learning_mode == 'HYBRID')" t-as="line">
                    <p>• Kursus: <t t-out="line.course_id.name"/> — <t t-out="line.hybrid_session_summary"/></p>
                </t>
                <p><em>Instruksi check-in akan dikirimkan terpisah melalui e-ticket.</em></p>
            </t>
            <p>Redeem code akan dikirimkan dalam lampiran terpisah oleh tim kami.</p>
            <p>Salam,<br/>Tim Sales IMPC</p>
        </field>
        <field name="auto_delete" eval="True"/>
    </record>

</odoo>
```

---

## FASE 5 — PDF Template Quotation B2B (Hari 4)

### Step 5.1 — Buat `report/quotation_b2b_report.xml`

```xml
<!-- report/quotation_b2b_report.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Daftarkan action report -->
    <record id="action_report_b2b_quotation" model="ir.actions.report">
        <field name="name">Quotation B2B Microcredential</field>
        <field name="model">sale.order</field>
        <field name="report_type">qweb-pdf</field>
        <field name="report_name">microcredential_sales.report_b2b_quotation_document</field>
        <field name="report_file">microcredential_sales.report_b2b_quotation_document</field>
        <field name="binding_model_id" ref="sale.model_sale_order"/>
        <field name="binding_type">report</field>
    </record>

    <!-- Template PDF -->
    <template id="report_b2b_quotation_document">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc">
                <t t-call="web.external_layout">
                    <div class="page">
                        <h2>Penawaran Kontrak B2B Microcredential</h2>
                        <p>Nomor: <strong><t t-out="doc.name"/></strong></p>
                        <p>Customer: <t t-out="doc.partner_id.name"/></p>
                        <p>Berlaku hingga: <t t-out="doc.validity_date"/></p>
                        <p>Periode Akses Kursus: <t t-out="doc.course_access_duration_days"/> hari</p>

                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Kursus</th>
                                    <th>Mode</th>
                                    <th>Jumlah Student</th>
                                    <th>Harga Satuan</th>
                                    <th>Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="doc.order_line" t-as="line">
                                    <tr>
                                        <td><t t-out="line.product_id.name"/>
                                            <t t-if="line.course_id">
                                                <br/><small>(<t t-out="line.course_id.name"/>)</small>
                                            </t>
                                        </td>
                                        <td><t t-out="line.learning_mode or '-'"/></td>
                                        <td><t t-out="line.student_count"/></td>
                                        <td><t t-out="line.price_unit"/> IDR</td>
                                        <td><t t-out="line.price_subtotal"/> IDR</td>
                                    </tr>
                                    <t t-if="line.learning_mode == 'HYBRID' and line.hybrid_session_summary">
                                        <tr>
                                            <td colspan="5" class="text-muted">
                                                <small>Jadwal Hybrid: <t t-out="line.hybrid_session_summary"/></small>
                                            </td>
                                        </tr>
                                    </t>
                                </t>
                            </tbody>
                        </table>

                        <div class="row">
                            <div class="col-6 offset-6">
                                <table class="table">
                                    <tr>
                                        <td><strong>Total</strong></td>
                                        <td><t t-out="doc.amount_total"/> IDR</td>
                                    </tr>
                                </table>
                            </div>
                        </div>

                        <div class="mt-5">
                            <p><em>Dokumen ini merupakan penawaran resmi dari IMPC. 
                            Dengan menandatangani, kedua pihak setuju dengan syarat dan ketentuan yang berlaku.</em></p>
                            <div class="row mt-5">
                                <div class="col-6 text-center">
                                    <p>___________________</p>
                                    <p>Tim Sales IMPC</p>
                                </div>
                                <div class="col-6 text-center">
                                    <p>___________________</p>
                                    <p><t t-out="doc.partner_id.name"/></p>
                                </div>
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

## FASE 6 — Views Contract (Hari 4–5)

### Step 6.1 — Buat `views/sale_order_contract_views.xml`

```xml
<!-- views/sale_order_contract_views.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Extend form view sale.order -->
    <record id="sale_order_contract_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.contract.form.inherit</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Tambahkan tab B2B Contract di bawah tab Order Lines -->
            <xpath expr="//notebook" position="inside">
                <page string="B2B Contract" attrs="{'invisible': [('contract_type','!=','B2B_CONTRACT')]}">
                    <group>
                        <group string="Informasi Kontrak">
                            <field name="contract_type" widget="radio"/>
                            <field name="partner_type"/>
                            <field name="contract_start_date"/>
                            <field name="contract_end_date"/>
                            <field name="course_access_duration_days"/>
                        </group>
                        <group string="Status">
                            <field name="approval_state" readonly="1"/>
                            <field name="contract_status"/>
                            <field name="approved_by" readonly="1"/>
                            <field name="approved_date" readonly="1"/>
                        </group>
                    </group>

                    <!-- Tombol Workflow -->
                    <div class="oe_button_box">
                        <button name="action_request_approval"
                                string="Kirim untuk Persetujuan"
                                type="object"
                                class="btn-primary"
                                attrs="{'invisible': [('approval_state','!=','draft')]}"/>
                        <button name="action_approve_contract"
                                string="Setujui Kontrak"
                                type="object"
                                class="btn-success"
                                groups="sales_team.group_sale_manager"
                                attrs="{'invisible': [('approval_state','!=','waiting_approval')]}"/>
                        <button name="action_reject_contract"
                                string="Tolak"
                                type="object"
                                class="btn-danger"
                                groups="sales_team.group_sale_manager"
                                attrs="{'invisible': [('approval_state','not in',['waiting_approval'])]}"/>
                        <button name="action_send_quotation"
                                string="Kirim Quotation ke Customer"
                                type="object"
                                class="btn-info"
                                attrs="{'invisible': [('approval_state','!=','approved')]}"/>
                    </div>
                </page>
            </xpath>

            <!-- Tambahkan field contract_type di header -->
            <xpath expr="//field[@name='partner_id']" position="after">
                <field name="contract_type" widget="radio" class="oe_inline"/>
            </xpath>

        </field>
    </record>

</odoo>
```

### Step 6.2 — Buat `views/sale_order_line_contract_views.xml`

> File ini ada di `__manifest__.py` tapi sering dilupakan. Berisi extend pada kolom tree order line untuk menampilkan `course_id`, `student_count`, dan `redeem_code_count` khusus untuk B2B.

```xml
<!-- views/sale_order_line_contract_views.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Extend tree view order line: tambahkan kolom B2B -->
    <record id="sale_order_line_contract_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.line.contract.form.inherit</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Tambahkan kolom course_id, student_count, redeem_code_count
                 di tree order_line — SETELAH kolom product_id -->
            <xpath expr="//field[@name='order_line']/tree/field[@name='product_id']" position="after">
                <field name="course_id" optional="show"
                       string="Kursus"
                       domain="[('website_published', '=', True)]"/>
            </xpath>

            <!-- Tambahkan kolom student_count sebelum product_uom_qty -->
            <xpath expr="//field[@name='order_line']/tree/field[@name='product_uom_qty']" position="before">
                <field name="student_count" optional="show"
                       string="Jml Student"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="redeem_code_count" optional="show"
                       string="Jml Redeem Code"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="redeem_code_expiry_days" optional="hide"
                       string="Masa Berlaku (hari)"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
            </xpath>

            <!-- Tambahkan field course_id di form line (detail) -->
            <xpath expr="//field[@name='order_line']/form//field[@name='product_id']" position="after">
                <field name="course_id"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="student_count"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="redeem_code_count"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="redeem_code_expiry_days"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
                <field name="redeem_code_notes"
                       attrs="{'invisible': [('order_id.contract_type', '!=', 'B2B_CONTRACT')]}"/>
            </xpath>

        </field>
    </record>

</odoo>
```

> **Catatan `_inherit` pada view XML**: View ini menggunakan `inherit_id` dan `xpath` untuk **extend** view native `sale.view_order_form` — bukan replace. Ini adalah padanan `_inherit` di Python, tetapi untuk XML/views.

---

## FASE 7 — Testing Dev 1 (Hari 5)

Checklist sebelum serahkan ke integrasi:

- [ ] Modul bisa di-install tanpa error
- [ ] Field `contract_type`, `partner_type`, `contract_start_date`, `contract_end_date` muncul di form
- [ ] State machine approval berjalan: draft → waiting_approval → approved → rejected
- [ ] Status B2B contract berjalan: draft → quotation_sent → confirmed
- [ ] Email quotation terkirim ke customer (gunakan test mode)
- [ ] PDF quotation bisa didownload, memuat semua field
- [ ] Restriction: kontrak B2B tidak bisa dikonfirmasi tanpa approval

---

---

# DEV 2 — Integration & API Layer

**Scope**: Menambahkan field `learning_mode`, ringkasan jadwal hybrid, dan membangun API client untuk generate redeem code beserta wizard retry dan audit log.

**Dependency**:
- `learning_mode` field: **SOFT DEPENDENCY** pada W-01 (Website). Untuk sementara gunakan hardcode enum `ONLINE/OFFLINE/HYBRID` — nanti sync otomatis dari `slide.channel` ketika Website selesai.
- Redeem code API: **SOFT DEPENDENCY** pada W-07 (Website API contract). Gunakan mock response dulu.
- Bisa mulai bersamaan dengan Dev 1. **Jangan edit** `sale_order_contract.py` atau `sale_order_line_contract.py`.

---

## FASE 1 — Field Learning Mode & Hybrid di Order Line (Hari 1–2)

### Step 1.1 — Buat `models/sale_order_integration.py`

```python
# models/sale_order_integration.py
import requests
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REDEEM_CODE_API_URL_PARAM = 'microcredential_sales.redeem_code_api_url'
REDEEM_CODE_API_KEY_PARAM = 'microcredential_sales.redeem_code_api_key'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── Mode Pembelajaran (sync read-only dari course) ────────────────────────
    learning_mode = fields.Selection(
        selection=[
            ('ONLINE', 'Online'),
            ('OFFLINE', 'Offline'),
            ('HYBRID', 'Hybrid'),
        ],
        string='Mode Pembelajaran',
        compute='_compute_learning_mode',
        store=True,
        readonly=True,
        help='Otomatis diambil dari data kursus. Edit di modul eLearning.',
    )

    hybrid_session_summary = fields.Text(
        string='Ringkasan Jadwal Sesi Hybrid',
        help='Diisi otomatis dari data sesi offline Website Group jika mode = HYBRID',
        readonly=True,
        compute='_compute_hybrid_session_summary',
        store=True,
    )

    @api.depends('course_id')
    def _compute_learning_mode(self):
        """
        Sync learning_mode dari slide.channel.
        CATATAN: Field `x_learning_mode` di slide.channel dibuat oleh Website Group (W-01).
        Jika belum ada, default ke 'ONLINE'.
        """
        for line in self:
            if line.course_id and hasattr(line.course_id, 'x_learning_mode'):
                line.learning_mode = line.course_id.x_learning_mode
            else:
                line.learning_mode = 'ONLINE'   # Default sampai Website Group selesai W-01

    @api.depends('course_id', 'learning_mode')
    def _compute_hybrid_session_summary(self):
        """
        Ambil ringkasan jadwal hybrid dari Website Group (W-12).
        CATATAN: Implementasi penuh menunggu Website Group selesai endpoint sync sesi.
        Untuk sementara, kosong jika belum ada.
        """
        for line in self:
            if line.learning_mode != 'HYBRID' or not line.course_id:
                line.hybrid_session_summary = False
                continue
            # TODO: Ganti dengan API call ke Website Group ketika W-12 selesai
            # Untuk sementara, nilai dikosongkan (akan diisi manual oleh Sales)
            if not line.hybrid_session_summary:
                line.hybrid_session_summary = False


class SaleOrderRedeemIntegration(models.Model):
    _inherit = 'sale.order'

    # ── Status Redeem Code ────────────────────────────────────────────────────
    redeem_codes_generated = fields.Boolean(
        string='Redeem Code Sudah Digenerate',
        default=False,
        copy=False,
        tracking=True,
    )
    redeem_code_batch_id = fields.Char(
        string='Batch ID Redeem Code',
        copy=False,
        readonly=True,
    )
    redeem_codes_requested_at = fields.Datetime(
        string='Waktu Request Generate',
        copy=False,
        readonly=True,
    )
    redeem_codes_generated_at = fields.Datetime(
        string='Waktu Generate Berhasil',
        copy=False,
        readonly=True,
    )
    redeem_code_batch_status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('GENERATED', 'Berhasil'),
            ('FAILED', 'Gagal'),
        ],
        string='Status Batch',
        default='PENDING',
        copy=False,
        readonly=True,
        tracking=True,
    )
    redeem_code_csv_url = fields.Char(
        string='URL Download CSV Redeem Code',
        copy=False,
        readonly=True,
    )

    # ── Tombol Trigger Manual ────────────────────────────────────────────────
    def action_open_redeem_code_wizard(self):
        """Buka wizard untuk trigger/retry generate redeem code."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Redeem Code',
            'res_model': 'redeem.code.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    def _call_redeem_code_api(self, course_id, quantity, expiry_days):
        """
        Panggil API Website Group untuk generate redeem code.
        
        Returns:
            dict: Response dari API {'batch_id', 'codes_generated', 'csv_url', 'status'}
        Raises:
            UserError: Jika API tidak dapat dihubungi atau response error
        """
        api_url = self.env['ir.config_parameter'].sudo().get_param(
            REDEEM_CODE_API_URL_PARAM, 
            default='http://localhost:8069/api/v1/elearning/redeem-codes/generate'
        )
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            REDEEM_CODE_API_KEY_PARAM,
            default=''
        )

        if not api_key:
            raise UserError(_(
                'API key untuk redeem code belum dikonfigurasi. '
                'Set parameter: %s'
            ) % REDEEM_CODE_API_KEY_PARAM)

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
        }
        payload = {
            'course_id': course_id,
            'quantity': quantity,
            'contract_id': self.id,
            'contract_reference': self.name,
            'expiry_days': expiry_days,
            'requested_by': self.env.user.login,
        }

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout saat menghubungi API redeem code. Silakan coba lagi.'))
        except requests.exceptions.ConnectionError:
            raise UserError(_('Tidak dapat terhubung ke API redeem code. Periksa koneksi jaringan.'))
        except requests.exceptions.HTTPError as e:
            raise UserError(_('API error: %s') % str(e))

    def action_generate_redeem_codes_auto(self):
        """
        Auto-trigger dari contract confirmation.
        Dipanggil setelah action_confirm() berhasil untuk B2B.
        """
        self.ensure_one()
        if self.contract_type != 'B2B_CONTRACT':
            return

        b2b_lines = self.order_line.filtered(
            lambda l: l.course_id and l.redeem_code_count > 0
        )
        if not b2b_lines:
            _logger.warning(
                'Sale Order %s dikonfirmasi sebagai B2B tapi tidak ada line dengan redeem code.',
                self.name,
            )
            return

        self.redeem_codes_requested_at = fields.Datetime.now()
        self.redeem_code_batch_status = 'PENDING'

        # Ambil line pertama sebagai referensi (1 course per contract untuk saat ini)
        # TODO: Extend untuk multi-course jika diperlukan
        line = b2b_lines[0]

        # Buat log audit
        log = self.env['redeem.code.request.log'].create({
            'sale_order_id': self.id,
            'course_id': line.course_id.id,
            'quantity_requested': line.redeem_code_count,
            'expiry_days': line.redeem_code_expiry_days,
            'status': 'PENDING',
            'requested_at': fields.Datetime.now(),
        })

        retry_count = 0
        max_retries = 3
        last_error = None

        while retry_count < max_retries:
            try:
                result = self._call_redeem_code_api(
                    course_id=line.course_id.id,
                    quantity=line.redeem_code_count,
                    expiry_days=line.redeem_code_expiry_days,
                )
                # Berhasil
                self.redeem_codes_generated = True
                self.redeem_code_batch_id = result.get('batch_id')
                self.redeem_codes_generated_at = fields.Datetime.now()
                self.redeem_code_batch_status = 'GENERATED'
                self.redeem_code_csv_url = result.get('csv_url')

                log.write({
                    'status': 'SUCCESS',
                    'batch_id': result.get('batch_id'),
                    'response_payload': str(result),
                    'completed_at': fields.Datetime.now(),
                })
                self.message_post(
                    body=_('Redeem code berhasil digenerate. Batch ID: %s') % result.get('batch_id'),
                )
                return
            except UserError as e:
                last_error = str(e)
                retry_count += 1
                _logger.warning(
                    'Percobaan %d/3 generate redeem code gagal untuk %s: %s',
                    retry_count, self.name, last_error,
                )

        # Semua retry gagal
        self.redeem_code_batch_status = 'FAILED'
        log.write({
            'status': 'FAILED',
            'error_message': last_error,
            'completed_at': fields.Datetime.now(),
        })
        self.message_post(
            body=_('GAGAL generate redeem code setelah 3 percobaan. Error: %s. Gunakan tombol Retry manual.') % last_error,
            subtype_xmlid='mail.mt_comment',
        )
```

### Step 1.2 — Override `action_confirm` untuk Auto-Trigger

> **MRO Chain — Wajib Dipahami Dev 2**
>
> Di Odoo, ketika beberapa class menggunakan `_inherit = 'sale.order'`, Python membangun MRO (Method Resolution Order) berdasarkan urutan load file di `models/__init__.py`. Untuk `action_confirm`:
>
> ```
> models/__init__.py load order:
>   1. sale_order_contract.py      → SaleOrderContract
>   2. sale_order_integration.py   → SaleOrderRedeemIntegration   ← load TERAKHIR = prioritas MRO PERTAMA
>
> Runtime call chain ketika action_confirm dipanggil:
>   SaleOrderRedeemIntegration.action_confirm()   ← dipanggil pertama
>       ↓ super()
>   SaleOrderContract.action_confirm()            ← approval check + set contract_status
>       ↓ super()
>   sale.order.action_confirm()                   ← Odoo native (konfirmasi order)
> ```
>
> **Konsekuensi**: File Dev 2 ini memanggil `super()` SEBELUM trigger redeem code. Jadi urutan eksekusinya:
> 1. Approval check (Dev 1) → raise UserError jika belum approved
> 2. Native confirm Odoo → order dikonfirmasi
> 3. Set contract_status = 'confirmed' + email (Dev 1)
> 4. Auto-trigger redeem code (Dev 2) ← baru jalan setelah semua di atas berhasil
>
> **JANGAN hapus `super()` call** — ini akan memutus chain dan Dev 1 logic tidak akan berjalan.

Tambahkan method berikut ke `SaleOrderRedeemIntegration`:

```python
    def action_confirm(self):
        """Override untuk auto-trigger redeem code generate setelah confirm B2B."""
        result = super().action_confirm()
        for order in self.filtered(lambda o: o.contract_type == 'B2B_CONTRACT'):
            # Auto trigger generate redeem code
            try:
                order.action_generate_redeem_codes_auto()
            except Exception as e:
                # Jangan batalkan konfirmasi, log saja
                _logger.error(
                    'Auto-generate redeem code gagal untuk %s: %s',
                    order.name, str(e),
                )
                order.message_post(
                    body=_('Perhatian: Auto-generate redeem code gagal. Silakan trigger manual.'),
                )
        return result
```

---

## FASE 2 — Audit Log Model (Hari 2)

### Step 2.1 — Buat `models/redeem_code_log.py`

```python
# models/redeem_code_log.py
from odoo import models, fields


class RedeemCodeRequestLog(models.Model):
    _name = 'redeem.code.request.log'
    _description = 'Log Request Generate Redeem Code'
    _order = 'requested_at desc'
    _rec_name = 'sale_order_id'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    course_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Kursus',
    )
    quantity_requested = fields.Integer(string='Jumlah Diminta')
    expiry_days = fields.Integer(string='Masa Berlaku (hari)')
    status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('SUCCESS', 'Berhasil'),
            ('FAILED', 'Gagal'),
        ],
        string='Status',
        default='PENDING',
    )
    batch_id = fields.Char(string='Batch ID')
    response_payload = fields.Text(string='Response API (raw)')
    error_message = fields.Text(string='Pesan Error')
    requested_at = fields.Datetime(string='Waktu Request')
    completed_at = fields.Datetime(string='Waktu Selesai')
```

---

## FASE 3 — Wizard Retry Manual (Hari 3)

### Step 3.0 — Setup `wizard/__init__.py`

> Folder `wizard/` membutuhkan `__init__.py` agar Python mengenalnya sebagai package. File `.py` wizard juga harus di-import di `__init__.py` modul utama.

```python
# wizard/__init__.py
from . import redeem_code_wizard
```

Kemudian update `__init__.py` utama modul:

```python
# microcredential_sales/__init__.py  (update baris import)
from . import models
from . import wizard      # ← Tambahkan baris ini
from . import controllers
```

### Step 3.1 — Buat `wizard/redeem_code_wizard.py`

```python
# wizard/redeem_code_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RedeemCodeWizard(models.TransientModel):
    _name = 'redeem.code.wizard'
    _description = 'Wizard Generate / Retry Redeem Code'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        readonly=True,
    )
    course_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Kursus',
        required=True,
    )
    quantity = fields.Integer(
        string='Jumlah Redeem Code',
        required=True,
        default=1,
    )
    expiry_days = fields.Integer(
        string='Masa Berlaku (hari)',
        required=True,
        default=90,
    )
    note = fields.Text(string='Catatan')

    @api.onchange('sale_order_id')
    def _onchange_sale_order(self):
        order = self.sale_order_id
        if order and order.order_line:
            b2b_line = order.order_line.filtered(lambda l: l.course_id)[0:1]
            if b2b_line:
                self.course_id = b2b_line.course_id
                self.quantity = b2b_line.redeem_code_count or b2b_line.student_count
                self.expiry_days = b2b_line.redeem_code_expiry_days

    def action_execute(self):
        """Jalankan generate redeem code secara manual."""
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            raise UserError(_('Sale order tidak ditemukan.'))

        result = order._call_redeem_code_api(
            course_id=self.course_id.id,
            quantity=self.quantity,
            expiry_days=self.expiry_days,
        )

        order.redeem_codes_generated = True
        order.redeem_code_batch_id = result.get('batch_id')
        order.redeem_code_batch_status = 'GENERATED'
        order.redeem_code_csv_url = result.get('csv_url')

        # Log audit
        self.env['redeem.code.request.log'].create({
            'sale_order_id': order.id,
            'course_id': self.course_id.id,
            'quantity_requested': self.quantity,
            'expiry_days': self.expiry_days,
            'status': 'SUCCESS',
            'batch_id': result.get('batch_id'),
            'response_payload': str(result),
            'requested_at': fields.Datetime.now(),
            'completed_at': fields.Datetime.now(),
        })

        order.message_post(
            body=_('Redeem code digenerate manual. Batch ID: %s. Oleh: %s. Catatan: %s') % (
                result.get('batch_id'), self.env.user.name, self.note or '-'
            ),
        )

        return {'type': 'ir.actions.act_window_close'}
```

### Step 3.2 — Buat `wizard/redeem_code_wizard.xml`

```xml
<!-- wizard/redeem_code_wizard.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_redeem_code_wizard_form" model="ir.ui.view">
        <field name="name">redeem.code.wizard.form</field>
        <field name="model">redeem.code.wizard</field>
        <field name="arch" type="xml">
            <form string="Generate Redeem Code">
                <group>
                    <field name="sale_order_id" readonly="1"/>
                    <field name="course_id"/>
                    <field name="quantity"/>
                    <field name="expiry_days"/>
                    <field name="note" placeholder="Alasan manual trigger (opsional)..."/>
                </group>
                <footer>
                    <button name="action_execute" type="object" string="Generate Sekarang" class="btn-primary"/>
                    <button string="Batal" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

---

## FASE 4 — Views Integration (Hari 4)

### Step 4.1 — Buat `views/sale_order_integration_views.xml`

```xml
<!-- views/sale_order_integration_views.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Extend order line: tambahkan kolom mode pembelajaran -->
    <record id="sale_order_line_integration_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.line.integration.form.inherit</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Tambahkan kolom Learning Mode di order lines tree -->
            <xpath expr="//field[@name='order_line']/tree/field[@name='product_uom_qty']" position="before">
                <field name="course_id" optional="show"/>
                <field name="learning_mode" optional="show" readonly="1"/>
                <field name="student_count" optional="show"
                       attrs="{'invisible': [('order_id.contract_type','!=','B2B_CONTRACT')]}"/>
                <field name="redeem_code_count" optional="show"
                       attrs="{'invisible': [('order_id.contract_type','!=','B2B_CONTRACT')]}"/>
            </xpath>

            <!-- Tambahkan panel Redeem Code Status di footer -->
            <xpath expr="//div[@name='oe_optional_fields']" position="after">
                <div attrs="{'invisible': [('contract_type','!=','B2B_CONTRACT')]}">
                    <separator string="Status Redeem Code"/>
                    <group>
                        <group>
                            <field name="redeem_code_batch_status" readonly="1"/>
                            <field name="redeem_code_batch_id" readonly="1"/>
                            <field name="redeem_codes_requested_at" readonly="1"/>
                            <field name="redeem_codes_generated_at" readonly="1"/>
                        </group>
                        <group>
                            <field name="redeem_code_csv_url" readonly="1" widget="url"/>
                        </group>
                    </group>
                    <div>
                        <button name="action_open_redeem_code_wizard"
                                string="Generate / Retry Redeem Code"
                                type="object"
                                class="btn-warning"
                                attrs="{'invisible': [('redeem_code_batch_status','=','GENERATED')]}"/>
                    </div>
                </div>
            </xpath>

        </field>
    </record>

    <!-- List view untuk Audit Log -->
    <record id="redeem_code_log_tree" model="ir.ui.view">
        <field name="name">redeem.code.request.log.tree</field>
        <field name="model">redeem.code.request.log</field>
        <field name="arch" type="xml">
            <tree string="Log Redeem Code" decoration-success="status=='SUCCESS'" decoration-danger="status=='FAILED'">
                <field name="sale_order_id"/>
                <field name="course_id"/>
                <field name="quantity_requested"/>
                <field name="status"/>
                <field name="batch_id"/>
                <field name="requested_at"/>
                <field name="completed_at"/>
                <field name="error_message"/>
            </tree>
        </field>
    </record>

    <!-- Action untuk Audit Log -->
    <record id="action_redeem_code_log" model="ir.actions.act_window">
        <field name="name">Log Redeem Code</field>
        <field name="res_model">redeem.code.request.log</field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- Menu item di Sales -->
    <menuitem id="menu_redeem_code_log"
              name="Log Redeem Code"
              parent="sale.sale_order_menu_root"
              action="action_redeem_code_log"
              sequence="50"/>

</odoo>
```

---

## FASE 5 — Konfigurasi API (Hari 4)

### Step 5.1 — Tambahkan System Parameters

Di Odoo Settings → Technical → System Parameters, buat 2 parameter:

| Key | Value (default) | Catatan |
|---|---|---|
| `microcredential_sales.redeem_code_api_url` | `http://localhost:8069/api/v1/elearning/redeem-codes/generate` | Ganti ke URL Website Group production |
| `microcredential_sales.redeem_code_api_key` | *(isi dengan API key dari Website Group)* | Jangan hardcode di source code |

### Step 5.2 — Mock Response untuk Testing (sebelum Website selesai)

Gunakan tool seperti Postman Mock Server atau tambahkan endpoint sementara di Odoo untuk simulasi response:

```python
# Di shell Odoo atau script test sementara
MOCK_RESPONSE = {
    "batch_id": "BATCH-TEST-001",
    "codes_generated": 10,
    "csv_url": "/web/content/batch-test-001.csv",
    "status": "SUCCESS",
    "generated_at": "2026-04-23T10:15:00Z"
}
```

---

## FASE 6 — Testing Dev 2 (Hari 5)

Checklist sebelum serahkan ke integrasi:

- [ ] Field `learning_mode` muncul di order line (read-only), sync dari `course_id`
- [ ] Field `hybrid_session_summary` muncul untuk line dengan mode HYBRID
- [ ] Field-field redeem code muncul di form order (batch_id, status, csv_url)
- [ ] Tombol "Generate / Retry" membuka wizard dengan data terisi otomatis
- [ ] Wizard bisa dieksekusi dan mengupdate field di sale.order
- [ ] Audit log `redeem.code.request.log` tercatat per eksekusi
- [ ] Retry max 3x berjalan saat API gagal
- [ ] Log chatter di sale.order muncul untuk setiap event (berhasil/gagal)
- [ ] API key tidak hardcode di kode (gunakan ir.config_parameter)

---

---

# DEV 3 — CRM, Portal & Dashboard

**Scope**: Extend partner/CRM, buat portal HR manager, bangun renewal workflow, dan buat contract performance dashboard.

**Dependency**:
- Portal jadwal hybrid (`S-05`): **HARD DEPENDENCY** pada W-12 (Website). Buat placeholder dulu, konten jadwal diisi nanti.
- Dashboard performa (`S-06`): **HARD DEPENDENCY** pada A-07 (Accounting reconciliation). Buat UI-nya dulu, data diisi setelah Accounting selesai.
- Bisa mulai bersamaan dengan Dev 1 dan Dev 2. **Jangan edit** file milik Dev 1 atau Dev 2.

---

## FASE 1 — Extended Partner (CRM) (Hari 1–2)

### Step 1.1 — Buat `models/res_partner_extended.py`

```python
# models/res_partner_extended.py
from odoo import models, fields


class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'

    # ── Tipe Perusahaan ───────────────────────────────────────────────────────
    company_type_microcredential = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Perusahaan – Departemen HR'),
            ('CORPORATE_OTHER', 'Perusahaan – Lainnya'),
        ],
        string='Tipe Partner (Microcredential)',
        default='INDIVIDUAL',
    )
    industry_type = fields.Selection(
        selection=[
            ('TECH', 'Teknologi'),
            ('FINANCE', 'Keuangan'),
            ('MANUFACTURING', 'Manufaktur'),
            ('EDUCATION', 'Pendidikan'),
            ('OTHER', 'Lainnya'),
        ],
        string='Industri',
    )
    employee_count = fields.Integer(
        string='Jumlah Karyawan',
    )
    training_budget_annual = fields.Float(
        string='Anggaran Training Tahunan (IDR)',
    )
    is_hr_partner_admin = fields.Boolean(
        string='Admin HR Portal',
        default=False,
        help='Jika True, user portal ini bisa lihat semua kontrak perusahaannya',
    )
    hr_contract_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='partner_id',
        string='Kontrak B2B',
        domain=[('contract_type', '=', 'B2B_CONTRACT')],
    )
```

### Step 1.2 — Buat `views/res_partner_views.xml`

```xml
<!-- views/res_partner_views.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="res_partner_microcredential_form_inherit" model="ir.ui.view">
        <field name="name">res.partner.microcredential.form.inherit</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <xpath expr="//notebook" position="inside">
                <page string="Microcredential B2B"
                      attrs="{'invisible': [('is_company','=',False)]}">
                    <group>
                        <group string="Profil Perusahaan">
                            <field name="company_type_microcredential"/>
                            <field name="industry_type"/>
                            <field name="employee_count"/>
                            <field name="training_budget_annual" widget="monetary"/>
                        </group>
                        <group string="Akses Portal">
                            <field name="is_hr_partner_admin"/>
                        </group>
                    </group>
                    <separator string="Kontrak B2B"/>
                    <field name="hr_contract_ids" readonly="1">
                        <tree>
                            <field name="name"/>
                            <field name="contract_status"/>
                            <field name="contract_start_date"/>
                            <field name="contract_end_date"/>
                            <field name="amount_total"/>
                        </tree>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

---

## FASE 2 — CRM Pipeline Data (Hari 2)

### Step 2.1 — Buat `data/crm_pipeline_data.xml`

```xml
<!-- data/crm_pipeline_data.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">

    <!-- Stage CRM untuk pipeline B2B Microcredential -->
    <record id="crm_stage_b2b_prospecting" model="crm.stage">
        <field name="name">Prospecting HR</field>
        <field name="sequence">1</field>
        <field name="probability">10</field>
    </record>

    <record id="crm_stage_b2b_qualification" model="crm.stage">
        <field name="name">Kualifikasi & Kebutuhan</field>
        <field name="sequence">2</field>
        <field name="probability">30</field>
    </record>

    <record id="crm_stage_b2b_proposal" model="crm.stage">
        <field name="name">Proposal & Quotation</field>
        <field name="sequence">3</field>
        <field name="probability">50</field>
    </record>

    <record id="crm_stage_b2b_negotiation" model="crm.stage">
        <field name="name">Negosiasi Kontrak</field>
        <field name="sequence">4</field>
        <field name="probability">70</field>
    </record>

    <record id="crm_stage_b2b_won" model="crm.stage">
        <field name="name">Kontrak Ditandatangani (Won)</field>
        <field name="sequence">5</field>
        <field name="probability">100</field>
        <field name="is_won" eval="True"/>
    </record>

    <record id="crm_stage_b2b_lost" model="crm.stage">
        <field name="name">Tidak Jadi (Lost)</field>
        <field name="sequence">10</field>
        <field name="probability">0</field>
    </record>

</odoo>
```

---

## FASE 3 — Renewal Workflow (Hari 2–3)

### Step 3.1 — Buat `models/sale_order_renewal.py`

```python
# models/sale_order_renewal.py
from datetime import timedelta
from odoo import models, fields, api, _


class SaleOrderRenewal(models.Model):
    _inherit = 'sale.order'

    expiry_date = fields.Date(
        string='Tanggal Kadaluarsa Kontrak',
        help='Untuk B2B: gunakan contract_end_date. Field ini untuk kalkulasi renewal.',
        compute='_compute_expiry_date',
        store=True,
    )
    renewal_opportunity = fields.Boolean(
        string='Peluang Renewal',
        compute='_compute_renewal_opportunity',
        store=True,
    )
    renewed_to_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Diperpanjang ke Kontrak',
        copy=False,
        readonly=True,
    )
    days_until_expiry = fields.Integer(
        string='Hari Menuju Kadaluarsa',
        compute='_compute_days_until_expiry',
    )

    @api.depends('contract_end_date')
    def _compute_expiry_date(self):
        for rec in self:
            rec.expiry_date = rec.contract_end_date

    @api.depends('expiry_date')
    def _compute_renewal_opportunity(self):
        today = fields.Date.today()
        threshold = today + timedelta(days=30)
        for rec in self:
            if rec.expiry_date and rec.contract_type == 'B2B_CONTRACT':
                rec.renewal_opportunity = rec.expiry_date <= threshold and rec.contract_status == 'ongoing'
            else:
                rec.renewal_opportunity = False

    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                delta = rec.expiry_date - today
                rec.days_until_expiry = delta.days
            else:
                rec.days_until_expiry = 0

    def action_create_renewal_quotation(self):
        """Buat quotation baru sebagai renewal dari kontrak ini."""
        self.ensure_one()
        new_order = self.copy({
            'name': self.env['ir.sequence'].next_by_code('sale.order'),
            'contract_status': 'draft',
            'approval_state': 'draft',
            'redeem_codes_generated': False,
            'redeem_code_batch_id': False,
            'redeem_code_batch_status': 'PENDING',
        })
        self.renewed_to_order_id = new_order
        self.message_post(
            body=_('Renewal quotation dibuat: %s') % new_order.name,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal Quotation',
            'res_model': 'sale.order',
            'res_id': new_order.id,
            'view_mode': 'form',
        }

    @api.model
    def _cron_flag_renewal_opportunities(self):
        """
        Cron job harian:
        Tandai kontrak B2B yang kadaluarsa dalam 30 hari.
        Kirim email notifikasi ke salesperson.
        """
        contracts_due = self.search([
            ('contract_type', '=', 'B2B_CONTRACT'),
            ('contract_status', '=', 'ongoing'),
            ('renewal_opportunity', '=', True),
        ])
        for contract in contracts_due:
            contract.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Renewal: Kontrak %s kadaluarsa %d hari lagi') % (
                    contract.name, contract.days_until_expiry,
                ),
                note=_('Hubungi %s untuk perpanjangan kontrak. Usage: periksa dashboard performa.') % (
                    contract.partner_id.name,
                ),
                user_id=contract.user_id.id or self.env.user.id,
            )
```

### Step 3.2 — Buat Cron Job di `data/crm_pipeline_data.xml`

Tambahkan di bagian bawah file `crm_pipeline_data.xml`:

```xml
<!-- Tambahkan di dalam <odoo> tag -->

<!-- Cron: Cek renewal opportunity setiap hari -->
<record id="ir_cron_renewal_check" model="ir.cron">
    <field name="name">Sales: Cek Peluang Renewal Kontrak B2B</field>
    <field name="model_id" ref="sale.model_sale_order"/>
    <field name="state">code</field>
    <field name="code">model._cron_flag_renewal_opportunities()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="numbercall">-1</field>
    <field name="active" eval="True"/>
</record>
```

---

## FASE 4 — Portal HR Manager (Hari 3–4)

### Step 4.1 — Buat `controllers/portal_hr_controller.py`

```python
# controllers/portal_hr_controller.py
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError


class HRPartnerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'b2b_contract_count' in counters:
            contract_count = request.env['sale.order'].sudo().search_count([
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
                ('contract_type', '=', 'B2B_CONTRACT'),
                ('contract_status', 'in', ['confirmed', 'ongoing']),
            ])
            values['b2b_contract_count'] = contract_count

        return values

    @http.route('/portal/contracts', type='http', auth='user', website=True)
    def portal_contracts_list(self, **kwargs):
        """Daftar semua kontrak B2B milik perusahaan HR manager."""
        partner = request.env.user.partner_id
        contracts = request.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('contract_type', '=', 'B2B_CONTRACT'),
        ], order='contract_start_date desc')

        return request.render('microcredential_sales.portal_contracts_list', {
            'contracts': contracts,
            'page_name': 'contracts',
        })

    @http.route('/portal/contracts/<int:order_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, order_id, **kwargs):
        """Detail satu kontrak: redeem codes, jadwal hybrid (read-only), progress."""
        try:
            contract = self._document_check_access('sale.order', order_id)
        except AccessError:
            return request.redirect('/portal/contracts')

        # Ambil data jadwal hybrid (placeholder sampai Website Group selesai W-12)
        hybrid_lines = contract.order_line.filtered(
            lambda l: l.learning_mode == 'HYBRID'
        )

        return request.render('microcredential_sales.portal_contract_detail', {
            'contract': contract,
            'hybrid_lines': hybrid_lines,
            'page_name': 'contract_detail',
        })
```

### Step 4.2 — Buat `views/portal_hr_templates.xml`

```xml
<!-- views/portal_hr_templates.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Halaman Daftar Kontrak -->
    <template id="portal_contracts_list" name="Portal HR: Daftar Kontrak">
        <t t-call="portal.portal_layout">
            <t t-set="breadcrumbs_searchbar" t-value="True"/>
            <t t-call="portal.portal_searchbar">
                <t t-set="title">Kontrak Microcredential Perusahaan Anda</t>
            </t>
            <div class="container mt-4">
                <t t-if="not contracts">
                    <div class="alert alert-info">Tidak ada kontrak aktif ditemukan.</div>
                </t>
                <t t-else="">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>No. Kontrak</th>
                                <th>Status</th>
                                <th>Tanggal Mulai</th>
                                <th>Tanggal Berakhir</th>
                                <th>Total Nilai</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="contracts" t-as="contract">
                                <tr>
                                    <td><t t-out="contract.name"/></td>
                                    <td>
                                        <span t-attf-class="badge badge-#{
                                            'success' if contract.contract_status == 'ongoing'
                                            else 'warning' if contract.contract_status == 'confirmed'
                                            else 'secondary'}">
                                            <t t-out="contract.contract_status"/>
                                        </span>
                                    </td>
                                    <td><t t-out="contract.contract_start_date"/></td>
                                    <td><t t-out="contract.contract_end_date"/></td>
                                    <td><t t-out="contract.amount_total"/> IDR</td>
                                    <td>
                                        <a t-attf-href="/portal/contracts/#{contract.id}"
                                           class="btn btn-sm btn-primary">Detail</a>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </t>
            </div>
        </t>
    </template>

    <!-- Halaman Detail Kontrak -->
    <template id="portal_contract_detail" name="Portal HR: Detail Kontrak">
        <t t-call="portal.portal_layout">
            <div class="container mt-4">
                <h3>Kontrak: <t t-out="contract.name"/></h3>
                <p class="text-muted">
                    Status: <strong><t t-out="contract.contract_status"/></strong> |
                    Periode: <t t-out="contract.contract_start_date"/> – <t t-out="contract.contract_end_date"/>
                </p>

                <!-- Informasi Kursus -->
                <h5 class="mt-4">Kursus dalam Kontrak</h5>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Kursus</th>
                            <th>Mode</th>
                            <th>Jumlah Slot</th>
                            <th>Redeem Code</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="contract.order_line" t-as="line">
                            <tr>
                                <td><t t-out="line.product_id.name"/></td>
                                <td>
                                    <span t-attf-class="badge badge-#{
                                        'info' if line.learning_mode == 'ONLINE'
                                        else 'warning' if line.learning_mode == 'HYBRID'
                                        else 'secondary'}">
                                        <t t-out="line.learning_mode or 'ONLINE'"/>
                                    </span>
                                </td>
                                <td><t t-out="line.student_count"/></td>
                                <td><t t-out="line.redeem_code_count"/></td>
                            </tr>
                        </t>
                    </tbody>
                </table>

                <!-- Jadwal Sesi Hybrid -->
                <t t-if="hybrid_lines">
                    <h5 class="mt-4">Jadwal Sesi Tatap Muka (Hybrid)</h5>
                    <div class="alert alert-warning">
                        <t t-foreach="hybrid_lines" t-as="hl">
                            <p><strong><t t-out="hl.course_id.name"/>:</strong>
                                <t t-out="hl.hybrid_session_summary or 'Jadwal akan diinformasikan oleh tim IMPC.'"/>
                            </p>
                        </t>
                    </div>
                </t>

                <!-- Status Redeem Code -->
                <h5 class="mt-4">Status Redeem Code</h5>
                <div class="row">
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <h6>Status Batch</h6>
                            <p><t t-out="contract.redeem_code_batch_status"/></p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <h6>Batch ID</h6>
                            <p><t t-out="contract.redeem_code_batch_id or 'Belum digenerate'"/></p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <h6>Download CSV</h6>
                            <t t-if="contract.redeem_code_csv_url">
                                <a t-att-href="contract.redeem_code_csv_url"
                                   class="btn btn-sm btn-success">Download Redeem Code</a>
                            </t>
                            <t t-else="">
                                <span class="text-muted">Belum tersedia</span>
                            </t>
                        </div>
                    </div>
                </div>

                <!-- Tombol Support -->
                <div class="mt-4">
                    <a href="mailto:support@impc.id" class="btn btn-outline-secondary">
                        Hubungi Support
                    </a>
                    <a href="/portal/contracts" class="btn btn-outline-primary ml-2">
                        Kembali ke Daftar Kontrak
                    </a>
                </div>
            </div>
        </t>
    </template>

</odoo>
```

---

## FASE 5 — Dashboard Performa Kontrak (Hari 5)

### Step 5.1 — Buat `views/sale_order_dashboard_views.xml`

```xml
<!-- views/sale_order_dashboard_views.xml -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Action untuk B2B Contract Dashboard -->
    <record id="action_b2b_contracts_dashboard" model="ir.actions.act_window">
        <field name="name">Dashboard Kontrak B2B</field>
        <field name="res_model">sale.order</field>
        <field name="view_mode">kanban,tree,form</field>
        <field name="domain">[('contract_type','=','B2B_CONTRACT')]</field>
        <field name="context">{
            'search_default_group_by_contract_status': 1
        }</field>
    </record>

    <!-- Kanban view untuk B2B Contract -->
    <record id="sale_order_b2b_kanban" model="ir.ui.view">
        <field name="name">sale.order.b2b.kanban</field>
        <field name="model">sale.order</field>
        <field name="arch" type="xml">
            <kanban default_group_by="contract_status" class="o_kanban_dashboard">
                <field name="id"/>
                <field name="name"/>
                <field name="partner_id"/>
                <field name="amount_total"/>
                <field name="contract_status"/>
                <field name="contract_start_date"/>
                <field name="contract_end_date"/>
                <field name="renewal_opportunity"/>
                <field name="redeem_code_batch_status"/>
                <field name="days_until_expiry"/>
                <templates>
                    <t t-name="kanban-box">
                        <div class="oe_kanban_card oe_kanban_global_click">
                            <div class="o_kanban_card_header">
                                <div class="o_kanban_card_header_title">
                                    <strong><field name="name"/></strong>
                                </div>
                            </div>
                            <div class="o_kanban_card_content">
                                <p><field name="partner_id"/></p>
                                <p>Nilai: <field name="amount_total" widget="monetary"/> IDR</p>
                                <p>Berakhir: <field name="contract_end_date"/></p>
                                <t t-if="record.renewal_opportunity.raw_value">
                                    <div class="alert alert-warning p-1">
                                        ⚠️ Renewal dalam <field name="days_until_expiry"/> hari!
                                    </div>
                                </t>
                                <t t-if="record.redeem_code_batch_status.raw_value == 'FAILED'">
                                    <div class="alert alert-danger p-1">
                                        ❌ Redeem code GAGAL digenerate
                                    </div>
                                </t>
                            </div>
                        </div>
                    </t>
                </templates>
            </kanban>
        </field>
    </record>

    <!-- Action untuk Renewal Pipeline -->
    <record id="action_renewal_pipeline" model="ir.actions.act_window">
        <field name="name">Kontrak Perlu Renewal</field>
        <field name="res_model">sale.order</field>
        <field name="view_mode">tree,form</field>
        <field name="domain">[
            ('contract_type','=','B2B_CONTRACT'),
            ('renewal_opportunity','=',True)
        ]</field>
    </record>

    <!-- Menu Sales → B2B Contracts -->
    <menuitem id="menu_b2b_dashboard"
              name="Dashboard B2B Contracts"
              parent="sale.sale_order_menu_root"
              action="action_b2b_contracts_dashboard"
              sequence="5"/>

    <menuitem id="menu_renewal_pipeline"
              name="Kontrak Perlu Renewal"
              parent="sale.sale_order_menu_root"
              action="action_renewal_pipeline"
              sequence="6"/>

</odoo>
```

---

## FASE 6 — Testing Dev 3 (Hari 5)

Checklist sebelum serahkan ke integrasi:

- [ ] Field partner extended muncul di tab `Microcredential B2B` pada form res.partner
- [ ] CRM stage B2B tersedia di pipeline
- [ ] Cron `_cron_flag_renewal_opportunities` berjalan dan membuat activity
- [ ] Field `renewal_opportunity` True untuk kontrak yang kadaluarsa ≤ 30 hari
- [ ] Tombol "Buat Renewal Quotation" menghasilkan draft order baru
- [ ] Portal `/portal/contracts` bisa diakses user portal HR
- [ ] Portal menampilkan list kontrak perusahaan dengan benar
- [ ] Portal detail kontrak menampilkan kursus, status redeem, jadwal hybrid (placeholder)
- [ ] Kanban B2B Dashboard tampil dengan grouping by contract_status
- [ ] Menu Dashboard B2B dan Renewal Pipeline muncul di Sales

---

---

# KOORDINASI ANTAR DEVELOPER

## Timeline Pengerjaan & Titik Sinkronisasi

```
MINGGU 1
────────────────────────────────────────────────────────────────────────
Hari 1-2:  Dev 1 ── Setup modul + model contract + state machine
           Dev 2 ── Sale order line fields (learning_mode, hybrid_summary)
           Dev 3 ── Extended partner + CRM stages data

           ▶ SYNC POINT HARI 2:
             - Dev 1 commit skeleton model/__init__.py (semua file placeholder)
             - Dev 2 bisa langsung mulai extend tanpa tunggu Dev 1 selesai
             - Dev 3 bisa langsung mulai tanpa tunggu siapapun

────────────────────────────────────────────────────────────────────────
Hari 3:    Dev 1 ── Email template + PDF quotation report
           Dev 2 ── Audit log model + wizard retry
           Dev 3 ── Renewal model + cron job

────────────────────────────────────────────────────────────────────────
Hari 4:    Dev 1 ── Views contract (form, approval buttons)
           Dev 2 ── Views integration (order line columns, redeem status panel)
           Dev 3 ── Portal controller + portal templates

────────────────────────────────────────────────────────────────────────
Hari 5:    Dev 1 ── Testing + fix + security access rules
           Dev 2 ── Konfigurasi API params + mock test + testing
           Dev 3 ── Dashboard views + menu + testing

MINGGU 2
────────────────────────────────────────────────────────────────────────
Hari 6-7:  INTEGRASI BERSAMA
           - Install modul ke environment staging bersama
           - Dev 1 pimpin end-to-end test B2B contract flow
           - Dev 2 pimpin test redeem code generate (dengan mock)
           - Dev 3 pimpin test portal HR + cron renewal

           ▶ SYNC POINT HARI 7:
             - Bug dari end-to-end dibagikan, masing-masing fix di domain sendiri

────────────────────────────────────────────────────────────────────────
Hari 8-9:  Menunggu / koordinasi dengan group lain:
           - Dev 2 update endpoint URL setelah Website Group W-07 selesai
           - Dev 2 test dengan real API Website
           - Dev 3 update hybrid_session_summary setelah Website W-12 selesai
           - Dev 3 update dashboard setelah Accounting A-07 selesai

────────────────────────────────────────────────────────────────────────
Hari 10:   Final testing semua fitur + dokumentasi
```

---

## Aturan Git Agar Tidak Konflik

### Branching Strategy

```
main
└── dev/sales-group        ← Branch utama Sales Group
    ├── dev/sales-dev1     ← Dev 1 bekerja di sini
    ├── dev/sales-dev2     ← Dev 2 bekerja di sini
    └── dev/sales-dev3     ← Dev 3 bekerja di sini
```

### Workflow

1. Setiap developer **buat branch dari** `dev/sales-group`
2. Push dan buat Pull Request ke `dev/sales-group` (bukan langsung ke `main`)
3. Minimal 1 developer lain harus review sebelum merge
4. Setelah merge ke `dev/sales-group`, hapus branch pribadi
5. Merge ke `main` hanya dilakukan setelah semua fitur Sales Group selesai dan diuji

### File Ownership (Tidak Boleh Edit Tanpa Koordinasi)

| File | Pemilik | Siapa yang Boleh Edit |
|---|---|---|
| `models/sale_order_contract.py` | Dev 1 | Dev 1 saja |
| `models/sale_order_line_contract.py` | Dev 1 | Dev 1 saja |
| `views/sale_order_contract_views.xml` | Dev 1 | Dev 1 saja |
| `data/mail_templates.xml` | Dev 1 | Dev 1 saja |
| `report/quotation_b2b_report.xml` | Dev 1 | Dev 1 saja |
| `models/sale_order_integration.py` | Dev 2 | Dev 2 saja |
| `models/redeem_code_log.py` | Dev 2 | Dev 2 saja |
| `wizard/redeem_code_wizard.py` | Dev 2 | Dev 2 saja |
| `views/sale_order_integration_views.xml` | Dev 2 | Dev 2 saja |
| `models/res_partner_extended.py` | Dev 3 | Dev 3 saja |
| `models/sale_order_renewal.py` | Dev 3 | Dev 3 saja |
| `controllers/portal_hr_controller.py` | Dev 3 | Dev 3 saja |
| `views/portal_hr_templates.xml` | Dev 3 | Dev 3 saja |
| `views/sale_order_dashboard_views.xml` | Dev 3 | Dev 3 saja |
| `data/crm_pipeline_data.xml` | Dev 3 | Dev 3 saja |
| `__manifest__.py` | Dev 1 | Koordinasi bersama |
| `models/__init__.py` | Dev 1 (init) | Update bersama lewat PR |
| `security/ir.model.access.csv` | Dev 1 (koordinasi) | Semua tambahkan lewat PR |

---

## File `security/ir.model.access.csv` (Dibuat Bersama)

Setiap developer tambahkan baris untuk model miliknya. File akhir:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sale_order_manager,sale.order.manager,sale.model_sale_order,sales_team.group_sale_manager,1,1,1,1
access_redeem_code_log_manager,redeem.code.log.manager,model_redeem_code_request_log,sales_team.group_sale_manager,1,1,1,0
access_redeem_code_log_user,redeem.code.log.user,model_redeem_code_request_log,base.group_user,1,0,0,0
access_redeem_code_wizard,redeem.code.wizard,model_redeem_code_wizard,sales_team.group_sale_manager,1,1,1,1
```

---

## Checklist Integrasi Akhir (Semua Dev)

- [ ] Modul dapat di-install dari nol tanpa error
- [ ] Tidak ada field / method yang namanya bentrok antar file
- [ ] B2B contract bisa dibuat dari awal sampai confirmed (Dev 1 pimpin)
- [ ] Redeem code generate trigger berjalan setelah confirm (Dev 2 pimpin)
- [ ] Portal HR dapat diakses dan menampilkan data benar (Dev 3 pimpin)
- [ ] Cron renewal membuat activity untuk kontrak yang akan expired (Dev 3 pimpin)
- [ ] Email konfirmasi terkirim saat kontrak confirmed (Dev 1 pimpin)
- [ ] Audit log terbuat untuk setiap request redeem code (Dev 2 pimpin)
- [ ] PDF quotation bisa didownload dan memuat semua field B2B (Dev 1 pimpin)

---

## Kontak Interface dengan Group Lain

Catat poin koordinasi berikut agar tidak salah asumsi:

| Interface | Owner Group | Yang Menunggu | Status Saat Ini |
|---|---|---|---|
| Field `x_learning_mode` di `slide.channel` | **Website Group (W-01)** | Dev 2 (untuk sync learning_mode) | 🟡 Gunakan default 'ONLINE' sampai W-01 selesai |
| API `POST /api/v1/elearning/redeem-codes/generate` | **Website Group (W-07)** | Dev 2 (untuk API client) | 🟡 Gunakan mock response |
| Data sesi hybrid per kursus | **Website Group (W-12)** | Dev 2 (untuk hybrid_session_summary), Dev 3 (untuk portal) | 🟡 Tampilkan placeholder |
| Invoice dari sale.order | **Accounting Group (A-06)** | Dev 1 (contract_status → invoice) | 🟡 Test link manual |
| Data reconciliation redeem | **Accounting Group (A-07)** | Dev 3 (untuk dashboard performa) | 🔴 Tunggu A-07 selesai |

**Legenda**: 🟢 Siap | 🟡 Gunakan mock/placeholder | 🔴 Hard dependency, tunggu output

---

*Dokumen ini adalah panduan teknis internal Sales Group. Update sesuai perkembangan implementasi.*
