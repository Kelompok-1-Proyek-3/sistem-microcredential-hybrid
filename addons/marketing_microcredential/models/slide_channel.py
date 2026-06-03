from odoo import api, fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    event_id = fields.Many2one(
        'event.event',
        string='Event Offline',
        help='Event offline yang di-link ke course hybrid.',
    )
    event_date = fields.Datetime(
        string='Tanggal Event',
        compute='_compute_event_info',
        store=True,
        readonly=True,
    )
    event_location = fields.Char(
        string='Lokasi Event',
        compute='_compute_event_info',
        store=True,
        readonly=True,
    )
    event_capacity = fields.Integer(
        string='Kapasitas Event',
        compute='_compute_event_info',
        store=True,
        readonly=True,
    )

    @api.depends('event_id', 'event_id.date_begin', 'event_id.address_inline', 'event_id.seats_max')
    def _compute_event_info(self):
        for record in self:
            event = record.event_id
            if event:
                record.event_date = event.date_begin
                record.event_location = event.address_inline
                record.event_capacity = event.seats_max
            else:
                record.event_date = False
                record.event_location = False
                record.event_capacity = 0
