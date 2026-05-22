import hashlib
import secrets
import string

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ImpcRedeemCode(models.Model):
    _name = 'impc.redeem.code'
    _description = 'IMPC Redeem Code / Voucher'
    _order = 'create_date desc'
    _rec_name = 'code'

    # === Code Identity ===
    code = fields.Char(
        string='Redeem Code',
        required=True,
        index=True,
        copy=False,
        help='Unique 16-character alphanumeric code (format: IMPC-XXXX-XXXX-XXXX).',
    )
    batch_id = fields.Many2one(
        'impc.redeem.code.batch',
        string='Batch',
        ondelete='cascade',
        help='The batch this code belongs to.',
    )

    # === Course Link ===
    course_id = fields.Many2one(
        'slide.channel',
        string='Course',
        required=True,
        help='The course this code grants access to.',
    )

    # === State Management ===
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('claimed', 'Claimed'),
            ('expired', 'Expired'),
            ('revoked', 'Revoked'),
        ],
        string='Status',
        default='active',
        required=True,
        index=True,
    )

    # === Claim Info ===
    claimed_by = fields.Many2one(
        'res.partner',
        string='Claimed By',
        readonly=True,
    )
    claimed_date = fields.Datetime(
        string='Claimed Date',
        readonly=True,
    )
    channel_partner_id = fields.Many2one(
        'slide.channel.partner',
        string='Enrollment Created',
        readonly=True,
        help='The enrollment record created when this code was claimed.',
    )

    # === Expiry ===
    expiry_date = fields.Date(
        string='Expiry Date',
        required=True,
        help='The code cannot be redeemed after this date.',
    )

    # === Related Fields ===
    company_id = fields.Many2one(
        related='batch_id.partner_id',
        string='Company',
        store=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Each redeem code must be unique.',
    )

    # === Business Logic ===
    def action_validate(self, partner=None):
        """Validate if this code can be redeemed.
        Returns dict with 'valid' boolean and 'message' string.
        """
        self.ensure_one()

        if self.state == 'claimed':
            return {'valid': False, 'message': 'This code has already been claimed.'}
        if self.state == 'expired':
            return {'valid': False, 'message': 'This code has expired.'}
        if self.state == 'revoked':
            return {'valid': False, 'message': 'This code has been revoked.'}
        if self.expiry_date and self.expiry_date < fields.Date.today():
            self.state = 'expired'
            return {'valid': False, 'message': 'This code has expired.'}
        if partner and self.course_id:
            existing = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', self.course_id.id),
                ('partner_id', '=', partner.id),
            ], limit=1)
            if existing:
                return {
                    'valid': False,
                    'message': 'You are already enrolled in this course.',
                }

        return {'valid': True, 'message': 'Code is valid.'}

    def action_claim(self, partner):
        """Claim this code for a partner, creating enrollment."""
        self.ensure_one()

        validation = self.action_validate(partner)
        if not validation['valid']:
            raise ValidationError(validation['message'])

        # Create enrollment
        enrollment = self.env['slide.channel.partner'].sudo().create({
            'channel_id': self.course_id.id,
            'partner_id': partner.id,
            'enrollment_type': 'b2b_voucher',
            'redeem_code_id': self.id,
        })

        # Update code state
        self.write({
            'state': 'claimed',
            'claimed_by': partner.id,
            'claimed_date': fields.Datetime.now(),
            'channel_partner_id': enrollment.id,
        })

        return enrollment

    @api.model
    def generate_code(self):
        """Generate a single unique code in format IMPC-XXXX-XXXX-XXXX."""
        chars = string.ascii_uppercase + string.digits
        while True:
            part1 = ''.join(secrets.choice(chars) for _ in range(4))
            part2 = ''.join(secrets.choice(chars) for _ in range(4))
            part3 = ''.join(secrets.choice(chars) for _ in range(4))
            code = f'IMPC-{part1}-{part2}-{part3}'
            if not self.search_count([('code', '=', code)]):
                return code

    @api.model
    def cron_expire_codes(self):
        """Scheduled action: mark expired codes."""
        expired_codes = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', fields.Date.today()),
        ])
        expired_codes.write({'state': 'expired'})
        return True
