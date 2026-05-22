from odoo import api, fields, models


class ImpcRedeemCodeBatch(models.Model):
    _name = 'impc.redeem.code.batch'
    _description = 'IMPC Redeem Code Batch'
    _order = 'create_date desc'

    name = fields.Char(
        string='Batch Name',
        required=True,
        help='Reference name for this batch of codes.',
    )
    course_id = fields.Many2one(
        'slide.channel',
        string='Course',
        required=True,
        help='The course these codes grant access to.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='B2B Company',
        help='The corporate partner who purchased this batch.',
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=10,
        help='Number of codes to generate.',
    )
    expiry_date = fields.Date(
        string='Default Expiry Date',
        required=True,
        help='Default expiration date for all codes in this batch.',
    )
    code_ids = fields.One2many(
        'impc.redeem.code',
        'batch_id',
        string='Generated Codes',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('generated', 'Generated'),
            ('distributed', 'Distributed'),
        ],
        string='Status',
        default='draft',
        required=True,
    )

    # === Computed ===
    codes_total = fields.Integer(
        string='Total Codes',
        compute='_compute_code_stats',
    )
    codes_claimed = fields.Integer(
        string='Claimed Codes',
        compute='_compute_code_stats',
    )
    codes_active = fields.Integer(
        string='Active Codes',
        compute='_compute_code_stats',
    )

    @api.depends('code_ids', 'code_ids.state')
    def _compute_code_stats(self):
        for record in self:
            codes = record.code_ids
            record.codes_total = len(codes)
            record.codes_claimed = len(codes.filtered(lambda c: c.state == 'claimed'))
            record.codes_active = len(codes.filtered(lambda c: c.state == 'active'))

    def action_generate_codes(self):
        """Generate codes for this batch."""
        self.ensure_one()
        RedeemCode = self.env['impc.redeem.code']

        codes_to_create = []
        for _ in range(self.quantity):
            codes_to_create.append({
                'code': RedeemCode.generate_code(),
                'batch_id': self.id,
                'course_id': self.course_id.id,
                'expiry_date': self.expiry_date,
                'state': 'active',
            })

        RedeemCode.create(codes_to_create)
        self.state = 'generated'
        return True

    def action_mark_distributed(self):
        """Mark batch as distributed."""
        self.ensure_one()
        self.state = 'distributed'
        return True
