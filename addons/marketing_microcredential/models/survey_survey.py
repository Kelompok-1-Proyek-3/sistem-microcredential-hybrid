from odoo import fields, models


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    nps_question_id = fields.Many2one(
        'survey.question',
        string='NPS Question',
        domain="[('survey_id', '=', id)]",
        help='Pilih pertanyaan NPS untuk perhitungan skor bulanan.',
    )
