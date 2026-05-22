from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GenerateRedeemCodesWizard(models.TransientModel):
    _name = 'impc.generate.redeem.codes.wizard'
    _description = 'Generate Redeem Codes Wizard'

    course_id = fields.Many2one(
        'slide.channel',
        string='Course',
        required=True,
        domain=[('is_published', '=', True)],
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='B2B Company',
        help='The corporate partner who purchased this batch.',
    )
    batch_name = fields.Char(
        string='Batch Name',
        required=True,
        help='Reference name for this batch.',
    )
    quantity = fields.Integer(
        string='Number of Codes',
        required=True,
        default=10,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        required=True,
        default=lambda self: fields.Date.today() + relativedelta(months=3),
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity < 1 or record.quantity > 10000:
                raise ValidationError('Quantity must be between 1 and 10,000.')

    def action_generate(self):
        """Generate redeem codes and create a batch."""
        self.ensure_one()

        batch = self.env['impc.redeem.code.batch'].create({
            'name': self.batch_name,
            'course_id': self.course_id.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'quantity': self.quantity,
            'expiry_date': self.expiry_date,
        })
        batch.action_generate_codes()

        # Return action to view the created batch
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generated Batch',
            'res_model': 'impc.redeem.code.batch',
            'res_id': batch.id,
            'view_mode': 'form',
            'target': 'current',
        }
