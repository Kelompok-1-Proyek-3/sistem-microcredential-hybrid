# models/sale_order_contract.py
# Owner: Dev 1 — Contract Core
# Scope: B2B contract fields, approval state machine, contract status workflow

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderContract(models.Model):
    _inherit = 'sale.order'

    # ── Tipe Kontrak ──────────────────────────────────────────────────────────
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

    # ── Periode Kontrak B2B ───────────────────────────────────────────────────
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

    # ── Status Approval ───────────────────────────────────────────────────────
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

    # ── Status Kontrak B2B (workflow lifecycle) ───────────────────────────────
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
        """Sales kirim ke approver untuk review."""
        self.ensure_one()
        if self.contract_type != 'B2B_CONTRACT':
            raise UserError(_('Approval hanya untuk kontrak B2B.'))
        self.approval_state = 'waiting_approval'
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

    # ── Aksi Contract Status Workflow ────────────────────────────────────────
    def action_send_quotation(self):
        """Kirim quotation ke customer → status quotation_sent."""
        self.ensure_one()
        self.contract_status = 'quotation_sent'
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
        """Tandai kontrak sebagai selesai."""
        self.ensure_one()
        self.contract_status = 'completed'

    # ── Override action_confirm ───────────────────────────────────────────────
    def action_confirm(self):
        """
        Override: kontrak B2B wajib approval sebelum bisa dikonfirmasi.
        Setelah confirm, kirim email konfirmasi ke customer.
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
