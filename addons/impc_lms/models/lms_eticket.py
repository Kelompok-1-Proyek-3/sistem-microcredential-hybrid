import hashlib
import hmac
import logging
from datetime import datetime, time, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LmsEticket(models.Model):
    _name = 'lms.eticket'
    _description = 'LMS E-ticket'
    _order = 'id desc'

    enrollment_id = fields.Many2one('lms.enrollment', required=True, index=True, ondelete='cascade')
    session_id = fields.Many2one('lms.offline_session', required=True, index=True, ondelete='cascade')
    token_hash = fields.Char(required=True, index=True)
    qr_code_image = fields.Binary()
    is_used = fields.Boolean(default=False)
    used_at = fields.Datetime()
    expires_at = fields.Datetime()

    _sql_constraints = [
        ('token_hash_unique', 'unique(token_hash)', 'Token hash must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('token_hash'):
                vals['token_hash'] = self._generate_token_hash(vals)
            if not vals.get('expires_at'):
                expires_at = self._compute_expires_at(vals)
                if expires_at:
                    vals['expires_at'] = expires_at
        return super().create(vals_list)

    def _generate_token_hash(self, vals):
        enrollment_id = vals.get('enrollment_id')
        session_id = vals.get('session_id')
        if not enrollment_id or not session_id:
            raise UserError('Enrollment and session are required to generate token hash.')
        message = f"{enrollment_id}:{session_id}"
        secret = self._get_hmac_secret()
        return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _compute_expires_at(self, vals):
        session_id = vals.get('session_id')
        if not session_id:
            return False
        session = self.env['lms.offline_session'].browse(session_id)
        if not session.session_date:
            return False
        expires_date = session.session_date + timedelta(days=1)
        return datetime.combine(expires_date, time(23, 59, 59))

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
