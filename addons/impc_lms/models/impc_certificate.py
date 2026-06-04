import hashlib
import hmac
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImpcCertificate(models.Model):
    _name = 'impc.certificate'
    _description = 'IMPC Certificate'
    _order = 'issued_date desc, id desc'

    learner_id = fields.Many2one('lms.learner', required=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='learner_id.partner_id', store=True, index=True)
    channel_id = fields.Many2one('slide.channel', required=True, index=True, ondelete='restrict')
    enrollment_id = fields.Many2one('lms.enrollment', required=True, index=True, ondelete='restrict')
    cert_hash = fields.Char(index=True)
    qr_code_image = fields.Binary()
    issued_date = fields.Date(default=fields.Date.today, required=True)
    is_revoked = fields.Boolean(default=False)
    pdf_file = fields.Binary()
    skill_synced = fields.Boolean(default=False)

    _sql_constraints = [
        ('cert_hash_unique', 'unique(cert_hash)', 'Certificate hash must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        certificates = super().create(vals_list)
        for cert, vals in zip(certificates, vals_list):
            if not vals.get('cert_hash'):
                cert._ensure_cert_hash()
            if 'skill_synced' not in vals:
                cert.skill_synced = cert._compute_initial_skill_synced()
        return certificates

    def _ensure_cert_hash(self):
        for cert in self.filtered(lambda record: not record.cert_hash):
            secret = cert._get_hmac_secret()
            message = f"{cert.learner_id.id}:{cert.channel_id.id}:{cert.issued_date}"
            cert.cert_hash = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _compute_initial_skill_synced(self):
        self.ensure_one()
        if not self.partner_id:
            return True
        employee_model = self.env['hr.employee']
        employee = employee_model.search([
            ('user_id.partner_id', '=', self.partner_id.id),
        ], limit=1)
        if employee:
            return False
        missing_user_employee = employee_model.search([
            ('user_id', '=', False),
            ('work_contact_id', '=', self.partner_id.id),
        ], limit=1)
        if missing_user_employee:
            _logger.warning(
                'Employee %s missing user_id for certificate %s.',
                missing_user_employee.id,
                self.id,
            )
            return False
        return True

    def _get_hmac_secret(self):
        params = self.env['ir.config_parameter'].sudo()
        secret = params.get_param('lms.hmac_secret')
        if not secret:
            secret = params.get_param('database.secret')
            if secret:
                _logger.warning('Using database.secret as HMAC fallback. Set lms.hmac_secret.')
        if not secret:
            raise UserError('Missing HMAC secret. Set system parameter lms.hmac_secret.')
        return secret
