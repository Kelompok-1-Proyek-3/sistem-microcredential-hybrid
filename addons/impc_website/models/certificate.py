import hashlib
import base64
import io

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class ImpcCertificate(models.Model):
    _name = 'impc.certificate'
    _inherit = 'impc.certificate'
    _description = 'IMPC Digital Certificate'
    _order = 'create_date desc'
    _rec_name = 'name'

    # === Certificate Identity ===
    name = fields.Char(
        string='Certificate Number',
        readonly=True,
        copy=False,
        default='New',
        help='Sequential certificate number (CERT-YYYY-XXXXX).',
    )
    verification_code = fields.Char(
        string='Verification Code',
        readonly=True,
        index=True,
        copy=False,
        help='SHA-256 hash for certificate verification.',
    )

    # === Links ===
    channel_partner_id = fields.Many2one(
        'slide.channel.partner',
        string='Enrollment',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Student',
        required=True,
    )
    channel_id = fields.Many2one(
        'slide.channel',
        string='Course',
        required=True,
    )

    # === Certificate Data ===
    completion_date = fields.Datetime(
        string='Completion Date',
        default=fields.Datetime.now,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('issued', 'Issued'),
            ('revoked', 'Revoked'),
        ],
        string='Status',
        default='draft',
        required=True,
    )

    # === QR Code & Attachment ===
    qr_code = fields.Binary(
        string='QR Code',
        attachment=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Certificate PDF',
        readonly=True,
    )

    # === Verification URL ===
    verification_url = fields.Char(
        string='Verification URL',
        compute='_compute_verification_url',
    )

    _verification_code_unique = models.Constraint(
        'UNIQUE(verification_code)',
        'Verification code must be unique.',
    )
    _channel_partner_unique = models.Constraint(
        'UNIQUE(channel_partner_id)',
        'Only one certificate per enrollment.',
    )

    def _compute_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.verification_code:
                record.verification_url = (
                    f'{base_url}/verify-certificate/{record.verification_code}'
                )
            else:
                record.verification_url = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'impc.certificate'
                ) or 'New'
        return super().create(vals_list)

    def _generate_verification_code(self):
        """Generate SHA-256 hash from partner_id + channel_id + completion_date."""
        self.ensure_one()
        raw = f'{self.partner_id.id}-{self.channel_id.id}-{self.completion_date}'
        return hashlib.sha256(raw.encode()).hexdigest()

    def _generate_qr_code(self):
        """Generate QR code image encoding the verification URL."""
        self.ensure_one()
        if not HAS_QRCODE:
            return False

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = f'{base_url}/verify-certificate/{self.verification_code}'

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue())

    def action_generate(self):
        """Generate verification code, QR code, and PDF certificate."""
        for record in self:
            # Generate verification code
            record.verification_code = record._generate_verification_code()

            # Generate QR code
            qr_data = record._generate_qr_code()
            if qr_data:
                record.qr_code = qr_data

            # Generate PDF via report engine
            report = self.env.ref('impc_website.action_report_certificate')
            pdf_content, _ = report._render_qweb_pdf(report.id, [record.id])

            # Store as ir.attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'{record.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'impc.certificate',
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })
            record.attachment_id = attachment.id
            record.state = 'issued'

    def action_revoke(self):
        """Revoke a certificate."""
        for record in self:
            record.state = 'revoked'

    @api.model
    def _issue_for_enrollment(self, enrollment):
        """Create or repair the digital certificate for a completed enrollment."""
        enrollment.ensure_one()

        learner = self.env['lms.learner'].sudo().search([
            ('partner_id', '=', enrollment.partner_id.id),
        ], limit=1)
        if not learner:
            learner = self.env['lms.learner'].sudo().create({
                'partner_id': enrollment.partner_id.id,
                'learner_type': 'b2c',
            })

        lms_enrollment = self.env['lms.enrollment'].sudo().search([
            ('learner_id', '=', learner.id),
            ('channel_id', '=', enrollment.channel_id.id),
        ], limit=1)

        certificate = self.sudo().search([
            ('channel_partner_id', '=', enrollment.id),
        ], limit=1)

        certificate_vals = {
            'channel_partner_id': enrollment.id,
            'partner_id': enrollment.partner_id.id,
            'channel_id': enrollment.channel_id.id,
            'learner_id': learner.id,
            'enrollment_id': lms_enrollment.id if lms_enrollment else False,
        }
        if certificate:
            needs_regeneration = (
                certificate.partner_id != enrollment.partner_id
                or certificate.channel_id != enrollment.channel_id
                or certificate.state != 'issued'
                or not certificate.attachment_id
            )
            certificate.write(certificate_vals)
        else:
            certificate = self.sudo().create(certificate_vals)
            needs_regeneration = True

        if needs_regeneration:
            certificate.action_generate()

        enrollment.sudo().write({
            'certificate_id': certificate.id,
            'certificate_pending': False,
        })
        return certificate

    @api.model
    def cron_generate_pending_certificates(self):
        """Scheduled action: generate certificates for enrollments with pending flag."""
        pending = self.env['slide.channel.partner'].sudo().search([
            '|',
            ('certificate_pending', '=', True),
            '&',
            ('certificate_id', '=', False),
            '|',
            ('member_status', '=', 'completed'),
            ('completion', '>=', 100),
        ])
        for enrollment in pending:
            if not enrollment.exam_unlocked:
                continue
            self._issue_for_enrollment(enrollment)
        return True
